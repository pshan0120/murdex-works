"""2026-11-17 오하린 오지목 위험 대응안 비교 (sim_tutorial.py 정본 기준)

안 1 진흙: 뒷골목 바닥이 흙탕물. 창고 바닥 격자무늬 자국과 정민재 안전화 홈에 진흙, 오하린 레인부츠는 물기만.
          → 바닥+레인부츠 짝이 오하린을 의심하는 대신 빼 준다. 바닥+안전화 짝은 조금 세진다.
안 2 단계 교환: 오하린 휴대폰 메모(뒷문 1507, 1차)와 사진첩(보험증권 사진, 2차)을 맞바꾼다.
안 3 정문 근거를 단서로: 정문 목격이 증언 확률이 아니라 단서처럼 늘 테이블에 있다고 가정(상한선 확인용).
"""
import random, sys, copy
sys.stdout.reconfigure(encoding="utf-8")
import sim_tutorial as s
SJ, JM, CY, OH = s.R
B1, B2 = copy.deepcopy(s.S1), copy.deepcopy(s.S2)
ORIG = s.pressure
OPT = {}


def patched(k, stage, variant, said, jit):
    p = ORIG(k, stage, variant, said, jit)
    if OPT.get("mud"):
        floor = 1 if "A3" in k else .5
        if {"A2", "K4"} <= k: p[OH] -= 1 * floor + .6   # 의심 짝을 지우고, 진흙이 없어 빠지는 쪽으로
        if {"A2", "K2"} <= k: p[JM] += .4                # 진흙까지 맞음
    return p


def reset():
    s.S1.clear(); s.S1.update(copy.deepcopy(B1)); s.S2.clear(); s.S2.update(copy.deepcopy(B2))
    OPT.clear(); s.FRONT_P = .5


def swap(a1, b2):
    s.S2[a1] = s.S1.pop(a1); s.S1[b2] = s.S2.pop(b2)


def go(name, n=20000):
    random.seed(9)
    res = [s.run(policy="strategic") for _ in range(n)]
    t1, t2 = s.top_rates(res, "p1"), s.top_rates(res, "p2")
    close = 0; second = {r: 0 for r in s.R}
    for x in res:
        p = x["p2"]; o = sorted(((v, r) for r, v in p.items() if r != JM), reverse=True)
        second[o[0][1]] += 1
        if p[JM] - o[0][0] < 1.0: close += 1
    print(f"[{name}]\n  1차 끝: " + " ".join(f"{r} {t1[r]/n*100:.0f}%" for r in s.R)
          + "\n  2차 끝: " + " ".join(f"{r} {t2[r]/n*100:.0f}%" for r in s.R)
          + f"\n  범인 다음: " + " ".join(f"{r} {second[r]/n*100:.0f}%" for r in s.R if r != JM)
          + f" | 차이 1점 미만 {close/n*100:.0f}%")


s.pressure = patched
reset(); go("현재")
reset(); OPT["mud"] = 1; go("안 1 진흙")
reset(); swap("L4", "S2"); go("안 2 메모↔사진첩")
reset(); OPT["mud"] = 1; swap("L4", "S2"); go("안 1 + 안 2")
reset(); s.FRONT_P = 1.0; go("안 3 정문 근거가 늘 나옴(상한선)")
reset(); OPT["mud"] = 1; s.FRONT_P = 1.0; go("안 1 + 안 3")
