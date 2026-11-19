"""2026-11-17 (2) 공유 100%·정문 증언 100% 기준 오하린 쏠림 대응안"""
import random, sys, copy
sys.stdout.reconfigure(encoding="utf-8")
import sim_tutorial as s
SJ, JM, CY, OH = s.R
B1 = copy.deepcopy(s.S1); ORIG = s.pressure; OPT = {}

def patched(k, stage, variant, said, jit):
    p = ORIG(k, stage, variant, said, jit)
    floor = 1 if "A3" in k else .5
    if OPT.get("boots") and {"A2", "K4"} <= k: p[OH] -= 1 * floor
    if OPT.get("elim") and {"A2", "A6"} <= k: p[OH] -= OPT["elim"]
    return p
s.pressure = patched

def go(name, n=20000):
    random.seed(9)
    res = [s.run(policy="strategic") for _ in range(n)]
    t1, t2 = s.top_rates(res, "p1"), s.top_rates(res, "p2")
    second = {r: 0 for r in s.R}
    for x in res:
        o = sorted(((v, r) for r, v in x["p2"].items() if r != JM), reverse=True); second[o[0][1]] += 1
    print(f"[{name}]\n  1차 끝: " + " ".join(f"{r} {t1[r]/n*100:.0f}%" for r in s.R)
          + "\n  2차 끝: " + " ".join(f"{r} {t2[r]/n*100:.0f}%" for r in s.R)
          + "\n  범인 다음: " + " ".join(f"{r} {second[r]/n*100:.0f}%" for r in s.R if r != JM))

def reset():
    s.S1.clear(); s.S1.update(copy.deepcopy(B1)); OPT.clear()

reset(); go("현재")
reset(); OPT["boots"] = 1; s.S1["K4"] = ("NOT:" + OH, False, {}); go("가: 오하린 레인부츠를 격자무늬가 아닌 밑창으로")
reset(); OPT["elim"] = .8; go("참고: 바닥 자국+정문 목격 소거를 플레이어가 확실히 해낸다고 볼 때(오하린 -0.8 더)")
reset(); s.S1["C5"] = ("NOT:" + "없음", True, {OH: 1.4}); go("나: 서류철에서 보험증권을 빼고 사진첩(2차)에만 남김")
reset(); OPT["boots"] = 1; s.S1["K4"] = ("NOT:" + OH, False, {}); s.S1["C5"] = (None, True, {OH: 1.4}); go("가 + 나")
