#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
단계_*.txt 안 대본(지시문+대사)을 순서대로 로컬 GPT-SoVITS API로 읽어
개별 WAV 파일로 생성하는 스크립트 (gen_voice_wav.py)

단계 파일 하나를 통째로 처리(전체 생성)할 수도 있고, --line 옵션으로
특정 줄 하나만 다시 만들 수도 있다(특정 wav만 이상하게 들릴 때 재생성용).
"""

import argparse
import json
import os
import re
import shutil
import sys

from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding="utf-8")


def parse_args():
    parser = argparse.ArgumentParser(
        description="단계_*.txt의 대본을 순서대로 TTS로 읽어 WAV 파일들을 생성합니다."
    )
    parser.add_argument("step_txt_path", help="단계_*.txt 파일 경로 (예: works/도플로이드/texts/단계_5_C구역_조사.txt)")
    parser.add_argument("--line", type=int, default=None, help="이 번호의 대사/지시문 한 줄만 다시 생성 (미지정 시 전체 생성)")
    parser.add_argument("--from", dest="from_line", type=int, default=None, help="이 번호부터 생성 (--to 없으면 끝까지). 예: 앞부분을 수작업으로 이미 만든 경우")
    parser.add_argument("--to", dest="to_line", type=int, default=None, help="--from과 함께 써서 이 번호까지만 생성 (범위 재생성용)")
    parser.add_argument("--voices", default=None, help="voices.json 경로 (미지정 시 <작품>/audios/voice/voices.json 자동 탐색)")
    parser.add_argument("--api-url", default="http://localhost:9872/", help="GPT-SoVITS Gradio API 주소")
    parser.add_argument("--dry-run", action="store_true", help="실제 생성 없이 몇 번째 줄이 누구 대사인지만 출력")
    return parser.parse_args()


def find_voices_json(step_txt_path, override):
    if override:
        return override
    # works/<작품명>/texts/단계_*.txt -> works/<작품명>/audios/voice/voices.json
    texts_dir = os.path.dirname(os.path.abspath(step_txt_path))
    work_dir = os.path.dirname(texts_dir)
    candidate = os.path.join(work_dir, "audios", "voice", "voices.json")
    if os.path.exists(candidate):
        return candidate
    raise FileNotFoundError(
        f"voices.json을 자동으로 찾지 못했습니다: {candidate}\n"
        f"--voices 옵션으로 직접 경로를 지정하세요."
    )


def extract_script_lines(html):
    """대본 낭독/마지막 대화 섹션 안의 script-direction, script-line을 문서 순서대로 추출.
    각 항목은 (kind, speaker, text) 튜플. kind는 'direction' 또는 'line'.
    지시문(direction)의 speaker는 항상 '나레이터'로 고정.
    """
    soup = BeautifulSoup(html, "html.parser")

    # "1. 대본 낭독" 또는 "1. 마지막 대화" section-title부터, 다음 section-title 전까지가 대본 구간
    section_titles = soup.find_all(class_="section-title")
    script_scope_start = None
    for st in section_titles:
        text = st.get_text(strip=True)
        if re.match(r"^1\.\s*(대본\s*낭독|마지막\s*대화)", text):
            script_scope_start = st
            break

    if script_scope_start is None:
        # section-title 구분이 없는 파일이면 전체를 대상으로 함
        nodes = soup.find_all(class_=["script-direction", "script-line"])
    else:
        nodes = []
        for sib in script_scope_start.find_all_next():
            classes = sib.get("class") or []
            if "section-title" in classes:
                break
            if "script-direction" in classes:
                nodes.append(sib)
            elif "script-line" in classes:
                nodes.append(sib)

    results = []
    for node in nodes:
        classes = node.get("class") or []
        if "script-direction" in classes:
            # get_text(strip=True)는 태그 경계에 붙어있던 진짜 공백까지 지워버릴 수 있어서
            # 태그 없는 원본 텍스트를 그대로 뽑은 뒤, 줄바꿈/들여쓰기만 하나의 공백으로 정리한다.
            text = re.sub(r"\s+", " ", node.get_text()).strip()
            if text:
                results.append(("direction", "나레이터", text))
        elif "script-line" in classes:
            char_span = node.find(class_=re.compile(r"^character-"))
            speaker = char_span.get_text(strip=True) if char_span else "알수없음"
            # "베일라: "따옴표 대사"" 형태에서 콜론 뒤 큰따옴표로 감싸인 대사만 추출
            full_text = re.sub(r"\s+", " ", node.get_text()).strip()
            quote_match = re.search(r'"([^"]*)"', full_text)
            text = quote_match.group(1).strip() if quote_match else re.sub(r"^.*?:\s*", "", full_text)
            text = strip_stage_directions(text)
            if text:
                results.append(("line", speaker, text))

    return results


def strip_stage_directions(text):
    """대사 안에 섞인 (연기 지시/지문) 괄호를 읽지 않도록 제거한다.
    예: '(마주 앉는 순간, 흠칫 놀라며) ...알렉스?' -> '...알렉스?'
    괄호 안에 다시 괄호가 없는 단순 케이스만 처리(대본에서 중첩 괄호는 쓰지 않음)."""
    cleaned = re.sub(r"[(（][^()（）]*[)）]", "", text)
    return re.sub(r"\s+", " ", cleaned).strip()


def resolve_speed(voices_cfg, step_basename, speaker):
    default_speed = voices_cfg["voices"][speaker]["speed"]
    overrides = voices_cfg.get("speed_overrides", {})
    step_overrides = overrides.get(step_basename, {})
    return step_overrides.get(speaker, default_speed)


def main():
    args = parse_args()

    if not os.path.exists(args.step_txt_path):
        print(f"[ERROR] 파일을 찾을 수 없습니다: {args.step_txt_path}")
        sys.exit(1)

    with open(args.step_txt_path, "r", encoding="utf-8") as f:
        content = f.read()

    desc_match = re.search(r'(<div class="story-content".*)', content, re.DOTALL)
    if not desc_match:
        print("[ERROR] '단계 설명' HTML(<div class=\"story-content\">...)을 찾지 못했습니다.")
        sys.exit(1)

    lines = extract_script_lines(desc_match.group(1))
    if not lines:
        print("[ERROR] 대본(지시문/대사)을 하나도 찾지 못했습니다.")
        sys.exit(1)

    voices_json_path = find_voices_json(args.step_txt_path, args.voices)
    with open(voices_json_path, "r", encoding="utf-8") as f:
        voices_cfg = json.load(f)
    output_dir = os.path.dirname(voices_json_path)

    step_basename = os.path.splitext(os.path.basename(args.step_txt_path))[0]

    print(f"[INFO] 대본 {len(lines)}줄 발견 ({step_basename})")
    unknown_speakers = {spk for _, spk, _ in lines if spk not in voices_cfg["voices"]}
    if unknown_speakers:
        print(f"[ERROR] voices.json에 등록되지 않은 화자: {sorted(unknown_speakers)}")
        print(f"        {voices_json_path} 의 'voices'에 먼저 추가하세요.")
        sys.exit(1)

    targets = list(enumerate(lines, start=1))
    if args.line is not None:
        targets = [(i, l) for i, l in targets if i == args.line]
        if not targets:
            print(f"[ERROR] {args.line}번 줄이 존재하지 않습니다 (총 {len(lines)}줄).")
            sys.exit(1)
    elif args.from_line is not None:
        to_line = args.to_line if args.to_line is not None else len(lines)
        targets = [(i, l) for i, l in targets if args.from_line <= i <= to_line]
        if not targets:
            print(f"[ERROR] {args.from_line}~{to_line}번 범위에 해당하는 줄이 없습니다 (총 {len(lines)}줄).")
            sys.exit(1)
    elif args.to_line is not None:
        print("[ERROR] --to는 --from과 함께 사용해야 합니다.")
        sys.exit(1)

    for idx, (kind, speaker, text) in targets:
        speed = resolve_speed(voices_cfg, step_basename, speaker)
        print(f"[{idx}/{len(lines)}] ({'지시문' if kind == 'direction' else speaker}) speed={speed} : {text[:40]}{'...' if len(text) > 40 else ''}")

    if args.dry_run:
        print("[DRY-RUN] 실제 생성은 하지 않았습니다.")
        return

    from gradio_client import Client, handle_file

    client = Client(args.api_url)
    loaded_models = (None, None)  # 매 줄마다 불필요하게 모델을 다시 로드하지 않기 위한 캐시

    def ensure_models_loaded(speaker):
        nonlocal loaded_models
        voice = voices_cfg["voices"][speaker]
        gpt_model = voice.get("gpt_model", voices_cfg["gpt_model"])
        sovits_model = voice.get("sovits_model", voices_cfg["sovits_model"])
        if (gpt_model, sovits_model) == loaded_models:
            return
        client.predict(gpt_path=gpt_model, api_name="/change_gpt_weights")
        client.predict(
            sovits_path=sovits_model,
            prompt_language=voices_cfg["language"],
            text_language=voices_cfg["language"],
            api_name="/change_sovits_weights",
        )
        loaded_models = (gpt_model, sovits_model)
        print(f"[INFO] 모델 전환: {speaker} 전용 ({gpt_model.split('/')[-1]} / {sovits_model.split('/')[-1]})"
              if "gpt_model" in voice or "sovits_model" in voice else f"[INFO] 모델 전환: 기본 모델")

    for idx, (kind, speaker, text) in targets:
        voice = voices_cfg["voices"][speaker]
        ref_audio_path = os.path.join(output_dir, voice["ref_audio"])
        speed = resolve_speed(voices_cfg, step_basename, speaker)
        ensure_models_loaded(speaker)

        result = client.predict(
            ref_wav_path=handle_file(ref_audio_path),
            prompt_text=voice["ref_text"],
            prompt_language=voices_cfg["language"],
            text=text,
            text_language=voices_cfg["language"],
            how_to_cut="자르지 않음",
            top_k=10,
            speed=speed,
            ref_free=False,
            api_name="/get_tts_wav",
        )

        out_path = os.path.join(output_dir, f"{step_basename}_{idx}.wav")
        shutil.copy(result, out_path)
        print(f"[{idx}/{len(lines)}] saved -> {out_path}")

    print(f"[DONE] {len(targets)}개 파일 생성 완료.")


if __name__ == "__main__":
    main()
