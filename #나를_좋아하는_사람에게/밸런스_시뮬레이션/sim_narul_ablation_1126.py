"""2026-11-26 재시뮬레이션에서 범인 1위가 49%→65%로 오른 원인을 하나씩 나눠 본다.
각 줄은 지금 정본(sim_narul.py)에서 한 가지만 11-17 값으로 되돌린 결과다.
실행: python sim_narul_ablation_1126.py
"""
import random, copy, sys, io, contextlib
import sim_narul as S

BASE = dict(CLUES=copy.deepcopy(S.CLUES), COMBOS=list(S.COMBOS), TESTIMONY=list(S.TESTIMONY), STAGES=list(S.STAGES))


def reset():
    S.CLUES.clear(); S.CLUES.update(copy.deepcopy(BASE["CLUES"]))
    S.COMBOS[:] = BASE["COMBOS"]; S.TESTIMONY[:] = BASE["TESTIMONY"]; S.STAGES[:] = BASE["STAGES"]


def last_top(n=10000):
    res = [S.run(policy="strategic") for _ in range(n)]
    t = S.top_rates([x["snaps"][-1]["p"] for x in res])
    te = S.top_rates([x["snaps"][-1]["pe"] for x in res])
    g10 = sum(1 for x in res if "G10" in x["hidden"]) / n
    return t, te, g10, n


def show(name):
    random.seed(7)
    t, te, g10, n = last_top()
    print(f"{name:34s} | 3단계 끝 1위 " + " ".join(f"{r} {t[r]/n*100:.0f}%" for r in S.R)
          + f" | 소거 포함 정형미 {te[S.JH]/n*100:.0f}% | G10 끝까지 숨김 {g10*100:.1f}%")


reset(); show("지금 정본")
reset(); S.STAGES[0] = ("조사 1단계", 9); show("AP 10→9 되돌림")
reset(); del S.CLUES["H3"]; del S.CLUES["J2"]; S.COMBOS[:] = [c for c in S.COMBOS if c[0] != {"A15", "J2"}]; show("H3·J2 빼기")
reset(); S.COMBOS[:] = [((c[0], c[1], .3, c[3]) if c[0] == {"A1", "A2", "R-1"} else c) for c in S.COMBOS]; show("불 꺼진 탕비실 .5→.3 되돌림")
reset(); S.CLUES["J2"] = (0, "NOT:" + S.JH, False, {S.JH: .3}); S.COMBOS[:] = [c for c in S.COMBOS if c[0] != {"A15", "J2"}]; show("J2를 A15와 겹치는 정보로 보고 .3만")
reset(); S.TESTIMONY[:] = [t for t in S.TESTIMONY if "끈을 돌려 던지는" not in t[6]]; show("장면 3 끈 지시문 빼기")
reset(); del S.CLUES["H3"]; del S.CLUES["J2"]
S.COMBOS[:] = [c for c in S.COMBOS if c[0] != {"A15", "J2"}]
S.COMBOS[:] = [((c[0], c[1], .3, c[3]) if c[0] == {"A1", "A2", "R-1"} else c) for c in S.COMBOS]
S.TESTIMONY[:] = [t for t in S.TESTIMONY if "끈을 돌려 던지는" not in t[6]]
S.STAGES[0] = ("조사 1단계", 9); show("모두 되돌림(11-17 재현 확인)")
