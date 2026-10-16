"""게화 어슐라 음성(audios/voice/*.wav)을 올리고 대본 줄의 audio_url 에 연결한다.

파일명: 엔딩_<n>.wav / 대면_<n>.wav (n 은 대본의 [n], DB line_order = n-1)
  python scripts/upload_gehwa_voice.py                       # 확인만
  python scripts/upload_gehwa_voice.py --apply               # 업로드 + 대면 줄 연결
  python scripts/upload_gehwa_voice.py --apply --ending      # 엔딩 줄까지 연결 (엔딩 재생 기능이 있을 때만)
이미 올린 파일은 등록_어슐라음성.json 의 주소를 재사용한다.
"""
import argparse, glob, json, os, re, sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8")

S = "7169e13b-5160-4a9b-9769-8ffd19763aa7"
ENDING_ID = "6676dbc9-0245-48cc-b665-fe194925b3bb"
CREATOR = "c6047a2e-222c-4f0e-b031-f639619888c0"
WORK = r"C:\dev\KLIEN\murdex\works\S-File\게화"
VOICE = os.path.join(WORK, "audios", "voice")
URLS = os.path.join(WORK, "등록_어슐라음성.json")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--ending", action="store_true")
    a = ap.parse_args()
    files = {}
    for p in sorted(glob.glob(os.path.join(VOICE, "*.wav"))):
        m = re.match(r"(엔딩|대면)_(\d+)\.wav$", os.path.basename(p))
        if m:
            files[(m.group(1), int(m.group(2)))] = p
    print("음성 파일", len(files), "개 (엔딩", sum(k[0] == "엔딩" for k in files), ", 대면", sum(k[0] == "대면" for k in files), ")")
    if not a.apply:
        return
    import requests
    from domain.auth.infrastructure.jwt_utils import JWTUtils
    from infrastructure.database.shared_connection_pool import SharedConnectionPool
    token = JWTUtils.create_access_token({"sub": CREATOR}, timedelta(minutes=40))
    done = json.load(open(URLS, encoding="utf-8")) if os.path.exists(URLS) else {}
    for (kind, n), p in files.items():
        key = f"{kind}_{n}"
        if key in done and done[key]["file"] == os.path.getsize(p):
            continue
        with open(p, "rb") as f:
            r = requests.post("http://localhost:8601/api/storage/upload/audio", params={"storyId": S},
                              files={"file": (f"ursula_{kind}_{n}.wav", f, "audio/wav")},
                              headers={"Authorization": f"Bearer {token}"}, timeout=300)
        r.raise_for_status()
        j = r.json()
        assert j.get("success"), j
        done[key] = {"url": j["data"]["url"], "file": os.path.getsize(p)}
        print("업로드", key)
        json.dump(done, open(URLS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    bad = [k for k, v in done.items() if requests.head(v["url"], timeout=30).status_code != 200]
    assert not bad, f"URL 응답 실패: {bad}"
    with SharedConnectionPool().get_connection() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT step_id FROM story_step WHERE story_id=%s AND step_name='대면'", (S,))
        step_id = cur.fetchone()["step_id"]
        targets = [("story_step_script_line", "step_id", step_id, "대면")]
        if a.ending:
            targets.append(("story_ending_script_line", "ending_id", ENDING_ID, "엔딩"))
        backup = {}
        for table, fk, pid, kind in targets:
            cur.execute(f"SELECT line_id, line_order, audio_url FROM {table} WHERE {fk}=%s", (pid,))
            backup[table] = cur.fetchall()
        json.dump(backup, open(os.path.join(WORK, "등록_백업", f"db_backup_voice_{datetime.now():%Y%m%d_%H%M%S}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        cur.execute("START TRANSACTION")
        try:
            for table, fk, pid, kind in targets:
                for (k, n) in sorted(files):
                    if k != kind:
                        continue
                    cur.execute(f"SELECT COUNT(*) c FROM {table} WHERE {fk}=%s AND line_order=%s AND speaker_type='NPC'", (pid, n - 1))
                    assert cur.fetchone()["c"] == 1, (kind, n)  # 줄 번호가 NPC 줄과 어긋나면 중단
                    cur.execute(f"UPDATE {table} SET audio_url=%s WHERE {fk}=%s AND line_order=%s AND speaker_type='NPC'",
                                (done[f"{kind}_{n}"]["url"], pid, n - 1))
            cur.execute("COMMIT")
        except Exception:
            cur.execute("ROLLBACK")
            raise
    print("COMMIT 완료:", ", ".join(t[3] for t in targets))


if __name__ == "__main__":
    main()
