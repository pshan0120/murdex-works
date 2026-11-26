"""2026-11-26 사용자 질문: 장소 단서(창고·카운터·뒷골목)도 조사 즉시 공개하지 않고 조사한 사람이 소유하면 밸런스가 어떻게 되나.

정본(sim_tutorial.py)의 공유 기준을 그대로 쓴다. 찾은 단서는 공개하되, 찾은 사람 자신에게 불리한 단서
(그 역할 무게 > 0)는 숨긴다(0.8, 범인 0.9). 바뀌는 점은 장소 단서도 이 기준을 거친다는 것 하나다.
장소 단서는 본인 조사 제한이 없으므로 자기에게 불리한 현장 단서를 본인이 집어 숨길 수 있다.
"""
import random, sys
from collections import Counter
sys.stdout.reconfigure(encoding="utf-8")
import sim_tutorial as s
SJ, JM, CY, OH = s.R
ORIG_S1, ORIG_S2 = dict(s.S1), dict(s.S2)
ORIG_P = s.pressure
OPT = {}

def set_owned(owned):
    for src, dst in ((ORIG_S1, s.S1), (ORIG_S2, s.S2)):
        for c, (lim, pub, w) in src.items():
            dst[c] = (lim, pub and not owned, w)

def patched(k, stage, variant, said, jit):
    p = ORIG_P(k, stage, variant, said, jit)
    if OPT.get("elim") and {"A2", "A6"} <= k:
        for r in (SJ, OH): p[r] -= .8
        if "B1" in k: p[CY] -= .8
    return p
s.pressure = patched

n = 20000
f = lambda t, m: " / ".join(f"{t[r]/m*100:.0f}" for r in s.R)
for owned in (False, True):
    set_owned(owned)
    print(f"\n#### {'장소 단서 소유' if owned else '지금(장소 단서 즉시 공개)'} — 전략적, 무게 ±20%, 서/정/최/오 의심 1위 % ####")
    for elim in (False, True):
        OPT["elim"] = elim
        random.seed(5)
        res = [s.run(policy="strategic", noise=.2) for _ in range(n)]
        print(f"{'소거 추리 해냄' if elim else '압박만'}: 1차 끝 {f(s.top_rates(res,'p1'), n)} | 2차 끝 {f(s.top_rates(res,'p2'), n)}")
    OPT["elim"] = False
    random.seed(5)
    res = [s.run(policy="strategic", noise=.2) for _ in range(n)]
    h = Counter(c for x in res for c in x["hidden"])
    print("끝까지 숨겨진 단서:", ", ".join(f"{c} {v/n*100:.0f}%" for c, v in h.most_common(10)))
    pf = sum(x["floor"] for x in res)/n; pd = sum(x["door"] for x in res)/n; pt = sum(x["truck"] for x in res)/n
    any_ = sum(x["floor"] or x["door"] or x["truck"] for x in res)/n
    print(f"풀이 경로: 바닥·신발 {pf*100:.0f}% / 출입 {pd*100:.0f}% / 블랙박스 {pt*100:.0f}% | 하나 이상 {any_*100:.0f}%")
    # 누가 무엇을 숨기나
    who = Counter()
    for x in res:
        pass
