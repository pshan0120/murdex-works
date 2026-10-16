"""게화 NPC 대사를 줄마다 WAV로 만든다 (GPT-SoVITS 9872 필요). 기본 화자는 어슐라이고 --speaker 로 다른 NPC(예: 어부)를 고른다.
화자는 voice/voices.json 의 voices 에 등록되어 있어야 한다(참고 음성 ref_audio, 참고 문장 ref_text, 속도 speed, 필요하면 gpt_model/sovits_model).
대사의 괄호 연기 지시는 읽지 않는다.

  python gen_ursula_voice.py --dry-run                      # 어슐라 대사 목록
  python gen_ursula_voice.py --speaker 어부 --dry-run       # 어부 대사 목록(voices.json 등록 전에도 확인 가능)
  python gen_ursula_voice.py --only 엔딩 --line 22          # 한 줄만
  python gen_ursula_voice.py --speaker 어부 --skip-existing # 어부 대사 전부(이미 있는 WAV는 건너뜀)
결과: voice/엔딩_<줄번호>.wav, voice/대면_<줄번호>.wav (줄번호는 대본의 [n]). 연결은 murdex-api/scripts/upload_gehwa_voice.py.
"""
import argparse, json, os, re, shutil, sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
TEXTS = os.path.join(os.path.dirname(HERE), "texts")
SOURCES = {"엔딩": "엔딩_대본.txt", "대면": "단계_2_대면.txt"}
DEFAULT_SPEAKER = "어슐라"


def npc_lines(path, speaker):
    t = open(path, encoding="utf-8").read().replace("\r\n", "\n")
    out = []
    pat = r"^\[(\d+)\] 화자 타입: NPC\n    화자: " + re.escape(speaker) + r"\n(?:.*\n)*?    대사: (.*)$"
    for m in re.finditer(pat, t, re.M):
        text = re.sub(r"[(（][^()（）]*[)）]", "", m.group(2))  # 연기 지시 괄호는 읽지 않는다
        text = re.sub(r"\s+", " ", text).strip()
        out.append((int(m.group(1)), text))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--speaker", default=DEFAULT_SPEAKER, help="NPC 화자 이름(기본: 어슐라)")
    ap.add_argument("--only", choices=list(SOURCES))
    ap.add_argument("--line", type=int)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--skip-existing", action="store_true", help="이미 있는 WAV는 건너뛴다")
    ap.add_argument("--api-url", default="http://localhost:9872/")
    a = ap.parse_args()
    cfg = json.load(open(os.path.join(HERE, "voice", "voices.json"), encoding="utf-8"))
    v = cfg["voices"].get(a.speaker)
    if v is None and not a.dry_run:
        sys.exit(f"voices.json 에 '{a.speaker}' 가 없습니다. voice/voices.json 의 voices 에 먼저 등록하세요.")
    jobs = []
    for key, fn in SOURCES.items():
        if a.only and a.only != key:
            continue
        for n, text in npc_lines(os.path.join(TEXTS, fn), a.speaker):
            if a.line and n != a.line:
                continue
            if a.skip_existing and os.path.exists(os.path.join(HERE, "voice", f"{key}_{n}.wav")):
                continue
            jobs.append((key, n, text))
    for key, n, text in jobs:
        print(f"{key} [{n}] speed={v['speed'] if v else '(미등록)'} : {text[:60]}{'...' if len(text) > 60 else ''}")
    print(f"{a.speaker} 대상 {len(jobs)}줄")
    if a.dry_run or not jobs:
        return
    from gradio_client import Client, handle_file
    c = Client(a.api_url)
    c.predict(gpt_path=v.get("gpt_model", cfg["gpt_model"]), api_name="/change_gpt_weights")
    c.predict(sovits_path=v.get("sovits_model", cfg["sovits_model"]), prompt_language=cfg["language"], text_language=cfg["language"], api_name="/change_sovits_weights")
    ref = os.path.join(HERE, "voice", v["ref_audio"])
    for key, n, text in jobs:
        r = c.predict(ref_wav_path=handle_file(ref), prompt_text=v["ref_text"], prompt_language=cfg["language"],
                      text=text, text_language=cfg["language"], how_to_cut="자르지 않음", top_k=10,
                      speed=v["speed"], ref_free=False, api_name="/get_tts_wav")
        out = os.path.join(HERE, "voice", f"{key}_{n}.wav")
        shutil.copy(r, out)
        print("saved", out)


if __name__ == "__main__":
    main()
