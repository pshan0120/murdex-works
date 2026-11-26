"""2026-11-26 "~에 대하여" 교체 뒤 재조정 안 예상치.
A: 정준희가 20:07 회의실로 돌아갈 때 노형철이 열린 창을 닫고 있는 것을 봄(정준희 타임라인 한 줄) → 노형철 기회 의심.
B: 정준희가 화장실에 있을 때 옆 남자화장실에서 물소리를 들음(정준희 타임라인 한 줄) → 유정석이 1층 화장실에 있었다는 말을 일부 받쳐 줌.
실행: python sim_narul_rebalance_1126.py
"""
import random
import sim_narul as S

BASE_T = list(S.TESTIMONY)


def show(name, n=10000):
    random.seed(9)
    res = [S.run(policy="strategic") for _ in range(n)]
    for si in (1, 2):
        t = S.top_rates([x["snaps"][si]["p"] for x in res])
        print(f"{name:14s} {S.STAGES[si][0]} 1위 " + " ".join(f"{r} {t[r]/n*100:.0f}%" for r in S.R))
    last = [x["snaps"][-1]["pe"] for x in res]
    te = S.top_rates(last)
    close = sum(1 for p in last if p[S.JH] - max(v for r, v in p.items() if r != S.JH) < 1.0) / n
    print(f"{'':14s} 소거 포함 3단계 1위 " + " ".join(f"{r} {te[r]/n*100:.0f}%" for r in S.R) + f" | 접전 {close*100:.0f}%")


A = (S.JJ, S.NH, .8, .9, set(), 0, "정준희: 20:07 돌아갈 때 노형철이 열린 창을 닫고 있었다")
B = (S.JJ, S.YJ, -.8, .9, set(), 0, "정준희: 화장실에 있을 때 옆 남자화장실에서 물소리")

S.TESTIMONY[:] = BASE_T; show("지금")
S.TESTIMONY[:] = BASE_T + [A]; show("A")
S.TESTIMONY[:] = BASE_T + [B]; show("B")
S.TESTIMONY[:] = BASE_T + [A, B]; show("A+B")
