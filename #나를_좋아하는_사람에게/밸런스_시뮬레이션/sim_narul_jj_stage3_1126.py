"""2026-11-26 정준희를 겨누는 1.5층 자료 후보 예상치(지금 정본 sim_narul.py 기준).
가: 여문혁의 메모 "2008년 인사 서류 원본은 문서고 맨 아래 칸" + 문서고에 원본이 없음 → 분류 일지(B6)로 2008년 자료를 꺼낸 정준희가 가져갔다. 정준희 사물함(W5)에 그 원본이 있다.
나: 정태호의 우편 속 사진 "우리 딸 일곱 살 생일 2008" → 나이로 정준희와 맞춰짐 + A8(하도훈이 "정 씨라서?").
실행: python sim_narul_jj_stage3_1126.py
"""
import random, copy
import sim_narul as S

BASE = dict(C=copy.deepcopy(S.CLUES), CO=list(S.COMBOS))


def reset():
    S.CLUES.clear(); S.CLUES.update(copy.deepcopy(BASE["C"])); S.COMBOS[:] = BASE["CO"]


def ga():
    S.CLUES["N11"] = (2, None, False, {S.JJ: .6})
    S.COMBOS.append(({"N11", "B6"}, S.JJ, .7, 2))
    S.COMBOS.append(({"N11", "W5"}, S.JJ, .6, 2))
    S.COMBOS.append(({"N11", "A8"}, S.JJ, .5, 2))


def na():
    S.CLUES["N12"] = (2, None, False, {S.JJ: .5})
    S.COMBOS.append(({"N12", "A8"}, S.JJ, .6, 2))


def show(name, n=10000):
    random.seed(21)
    res = [S.run(policy="strategic") for _ in range(n)]
    for si in (1, 2):
        t = S.top_rates([x["snaps"][si]["p"] for x in res])
        print(f"{name:10s} {S.STAGES[si][0]} 1위 " + " ".join(f"{r} {t[r]/n*100:.0f}%" for r in S.R))
    last = [x["snaps"][-1]["pe"] for x in res]
    te = S.top_rates(last)
    close = sum(1 for p in last if p[S.JH] - max(v for r, v in p.items() if r != S.JH) < 1.0) / n
    avg = {r: sum(x["snaps"][-1]["p"][r] for x in res) / n for r in S.R}
    print(f"{'':10s} 소거 포함 3단계 1위 " + " ".join(f"{r} {te[r]/n*100:.0f}%" for r in S.R) + f" | 접전 {close*100:.0f}% | 합계 " + " ".join(f"{r} {avg[r]:.1f}" for r in S.R))


reset(); show("지금")
reset(); ga(); show("가")
reset(); na(); show("나")
reset(); ga(); na(); show("가+나")
