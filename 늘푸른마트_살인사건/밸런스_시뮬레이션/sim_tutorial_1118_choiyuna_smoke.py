"""2026-11-18 테스트 40차 4번(최유나 담배 5분)과 장부 "한빛" 삭제 반영 뒤 정본 결과 (무게 ±20%)

소거 추리 참고값: 바닥(A2)+도어락(A6)이 나오면 서지훈·오하린 -0.8. 최유나는 정문으로 나갔으므로
슬리퍼(S1)나 POS 02:25(B1, 3분 거리 계산)까지 나와야 -0.8(2026-11-18부터).
"""
import random, sys
sys.stdout.reconfigure(encoding="utf-8")
import sim_tutorial as s
SJ, JM, CY, OH = s.R
ORIG = s.pressure
OPT = {}


def patched(k, stage, variant, said, jit):
    p = ORIG(k, stage, variant, said, jit)
    if OPT.get("elim") and {"A2", "A6"} <= k:
        for r in (SJ, OH): p[r] -= .8
        if "S1" in k or "B1" in k: p[CY] -= .8
    return p


s.pressure = patched
n = 20000
out = []
for elim in (False, True):
    OPT["elim"] = elim
    random.seed(5)
    res = [s.run(policy="strategic", noise=.2) for _ in range(n)]
    a = [x for x in res if x["action"]]
    out.append((s.top_rates(res, "p1"), s.top_rates(res, "p2"), s.top_rates(a, "p2")[JM] / len(a)))
f = lambda t: " ".join(f"{r} {t[r]/n*100:.0f}%" for r in s.R)
print(f"1차 끝: {f(out[0][0])}\n2차 끝: {f(out[0][1])}\n소거 추리 해냄 2차 끝: {f(out[1][1])}\n액션 쓴 판 정민재: 압박만 {out[0][2]*100:.0f}% / 소거 추리 {out[1][2]*100:.0f}%")
