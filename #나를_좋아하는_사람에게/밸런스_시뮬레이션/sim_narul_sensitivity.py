"""조사 2단계 뒤 '재해석' 가정이 결과를 얼마나 좌우하는지 보는 민감도 확인 (2026-11-17)
정본 sim_narul.py 를 불러와 가정만 바꿔 돌린다.
"""
import random, sys, statistics as st
sys.stdout.reconfigure(encoding="utf-8")
import sim_narul as s


def quick(name, n=10000):
    random.seed(3)
    res = [s.run("strategic") for _ in range(n)]
    for si in (1, 2):
        te = s.top_rates([x["snaps"][si]["pe"] for x in res])
        avg = {r: st.mean(x["snaps"][si]["pe"][r] for x in res) for r in s.R}
        print(f"[{name}] {s.STAGES[si][0]} 끝(소거 포함) 1위: " + " ".join(f"{r} {te[r]/n*100:.0f}%" for r in s.R)
              + " | 평균 " + " ".join(f"{r} {avg[r]:.1f}" for r in s.R))
    close = sum(1 for x in res if (lambda p: p[s.CULPRIT] - max(v for r, v in p.items() if r != s.CULPRIT) < 1)(x["snaps"][-1]["pe"]))
    print(f"   마지막 범인-2위 1점 미만 {close/n*100:.0f}%")


if __name__ == "__main__":
    base = dict(s.STAGE_MULT[1])
    quick("기준")
    s.STAGE_MULT[1] = dict(base, J1=1.0); s.STAGE_MULT[2] = s.STAGE_MULT[1]
    quick("J1은 장면 3 전까지 배수 없음")
    s.STAGE_MULT[1] = {}; s.STAGE_MULT[2] = {}
    quick("재해석 없음(배수 전부 끔)")
    s.BOARD = [b for b in s.BOARD if not b[0].startswith("R8")]
    quick("재해석 없음 + 던지기 이력 게시판 못 찾음")
