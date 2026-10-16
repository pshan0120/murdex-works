"""게화 어슐라 NPC 대사를 줄마다 WAV로 만든다 (GPT-SoVITS 9872 필요).

  python gen_ursula_voice.py --dry-run                 # 대상 줄 목록
  python gen_ursula_voice.py --only 엔딩 --line 22     # 한 줄만
  python gen_ursula_voice.py                           # 엔딩+대면 전부
결과: voice/엔딩_<줄번호>.wav, voice/대면_<줄번호>.wav (줄번호는 대본의 [n])
"""
import argparse, json, os, re, shutil, sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
TEXTS = os.path.join(os.path.dirname(HERE), "texts")
SOURCES = {"엔딩": "엔딩_대본.txt", "대면": "단계_2_대면.txt"}
SPEAKER = "어슐라"


def ursula_lines(path):
    t = open(path, encoding="utf-8").read().replace("\r\n", "\n")
    out = []
    for m in re.finditer(r"^\[(\d+)\] 화자 타입: NPC\n    화자: 어슐라\n(?:.*\n)*?    대사: (.*)$", t, re.M):
        text = re.sub(r"[(（][^()（）]*[)）]", "", m.group(2))  # 연기 지시 괄호는 읽지 않는다
        text = re.sub(r"\s+", " ", text).strip()
        out.append((int(m.group(1)), text))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=list(SOURCES))
    ap.add_argument("--line", type=int)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--skip-existing", action="store_true", help="이미 있는 WAV는 건너뛴다")
    ap.add_argument("--api-url", default="http://localhost:9872/")
    a = ap.parse_args()
    cfg = json.load(open(os.path.join(HERE, "voice", "voices.json"), encoding="utf-8"))
    v = cfg["voices"][SPEAKER]
    jobs = []
    for key, fn in SOURCES.items():
        if a.only and a.only != key:
            continue
        for n, text in ursula_lines(os.path.join(TEXTS, fn)):
            if a.line and n != a.line:
                continue
            if a.skip_existing and os.path.exists(os.path.join(HERE, "voice", f"{key}_{n}.wav")):
                continue
            jobs.append((key, n, text))
    for key, n, text in jobs:
        print(f"{key} [{n}] speed={v['speed']} : {text[:50]}{'...' if len(text) > 50 else ''}")
    print(f"대상 {len(jobs)}줄")
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
