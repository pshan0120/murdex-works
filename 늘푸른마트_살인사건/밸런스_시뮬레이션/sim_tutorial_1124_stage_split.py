"""2026-11-24 1차 단서(20장)와 2차 단서(8장) 비율 조정안 비교 (sim_tutorial.py 정본, 무게 ±20%)

현재: 1차 20장 AP 5, 2차 8장 AP 2 (정민재 액션 1 AP)
가: 용의자마다 동기 단서 하나씩 2차로 (C4 현금 점검표, C3 전표 사본·통장, C5 양도 계약서, L3 수진 메시지). 1차 16장 AP 4, 2차 12장 AP 3
나: 카운터 서류 셋(C4, C3, C5) + 소화기 거치대(A8)를 2차로. 1차 16장 AP 4, 2차 12장 AP 3
다: 가와 같이 옮기고 1차 AP는 5 그대로(1차를 다 보게), 2차 AP 3

소거 추리 참고값은 sim_tutorial_1118_choiyuna_smoke.py와 같다.
"""
import random, sys, copy
from statistics import mean
sys.stdout.reconfigure(encoding="utf-8")
import sim_tutorial as s
SJ, JM, CY, OH = s.R
B1, B2 = copy.deepcopy(s.S1), copy.deepcopy(s.S2)
ORIG = s.pressure
OPT = {}


def patched(k, stage, variant, said, jit):
    p = ORIG(k, stage, variant, said, jit)
    if OPT.get("elim") and {"A2", "A6"} <= k:
        for r in (SJ, OH): p[r] -= .8
        if "S1" in k or "B1" in k: p[CY] -= .8
    return p


s.pressure = patched


def move(codes):
    s.S1.clear(); s.S1.update(copy.deepcopy(B1)); s.S2.clear(); s.S2.update(copy.deepcopy(B2))
    for c in codes:
        s.S2[c] = s.S1.pop(c)


def go(name, codes, ap1, ap2, n=20000):
    move(codes)
    out = []
    for elim in (False, True):
        OPT["elim"] = elim
        random.seed(5)
        res = [s.run(policy="strategic", noise=.2, ap1=ap1, ap2=ap2) for _ in range(n)]
        a = [x for x in res if x["action"]]
        out.append((s.top_rates(res, "p1"), s.top_rates(res, "p2"), s.top_rates(a, "p2")[JM] / len(a),
                    mean(len(x["unfound1"]) for x in res), mean(len(x["unfound2"]) for x in res)))
    f = lambda t: " / ".join(f"{t[r]/n*100:.0f}" for r in s.R)
    print(f"[{name}] 1차 {len(s.S1)}장 AP {ap1}, 2차 {len(s.S2)}장 AP {ap2}"
          f"\n  1차 끝 서/정/최/오: {f(out[0][0])}\n  2차 끝: {f(out[0][1])}\n  소거 추리 2차 끝: {f(out[1][1])}"
          f"\n  액션 쓴 판 정민재: 압박만 {out[0][2]*100:.0f}% / 소거 {out[1][2]*100:.0f}%"
          f"\n  못 본 단서 평균: 1차 {out[0][3]:.2f}장, 2차 {out[0][4]:.2f}장")


go("현재", [], 5, 2)
go("가: 동기 단서 하나씩", ["C4", "C3", "C5", "L3"], 4, 3)
go("나: 카운터 서류 셋 + 거치대", ["C4", "C3", "C5", "A8"], 4, 3)
go("다: 가 + 1차 AP 5 유지", ["C4", "C3", "C5", "L3"], 5, 3)


# 라: 용의자마다 옮길 동기 단서 조합을 모두 비교(정민재는 C3 고정, 1차 AP 4, 2차 AP 3)
def quick(codes, ap1=4, ap2=3, n=6000):
    move(codes)
    OPT["elim"] = False
    random.seed(5)
    res = [s.run(policy="strategic", noise=.2, ap1=ap1, ap2=ap2) for _ in range(n)]
    t1, t2 = s.top_rates(res, "p1"), s.top_rates(res, "p2")
    f = lambda t: " / ".join(f"{t[r]/n*100:3.0f}" for r in s.R)
    spread = max(t1[r] for r in (SJ, CY, OH)) / n * 100
    print(f"  {'+'.join(codes):18s} 1차 {f(t1)} | 2차 {f(t2)} | 1차 최고 {spread:.0f}%")


if "--combos" in sys.argv:
    import itertools
    print("[라] 옮길 조합(서/정/최/오 1위 %)")
    for sj, cy, oh in itertools.product(["C4", "L1"], ["D1", "L3"], ["C5", "L4"]):
        quick([sj, "C3", cy, oh])


# 마~아: 동기 무게는 1차에 두고 정민재 쪽·중립 단서를 옮기는 조합
if "--neutral" in sys.argv:
    print("[중립 조합] 1차 AP 4, 2차 AP 3 (서/정/최/오 1위 %)")
    quick([], 5, 2)
    for codes in (["A4", "A8", "C3", "C1"], ["A4", "A8", "C3", "N2"], ["A4", "A8", "C3", "K1"], ["A4", "C3", "N2", "C1"],
                  ["A4", "A8", "N2", "K1"], ["A4", "C3", "C4", "C5"]):
        quick(codes)


# 마: 담배 상자·전표(A4), 소화기 거치대·고무장화(A8), 전표 사본·통장(C3), 지갑의 ATM 명세표(N2)를 2차로
if "--ma" in sys.argv:
    go("마: A4+A8+C3+N2를 2차로", ["A4", "A8", "C3", "N2"], 4, 3)


# 2026-11-24 확인: DB의 1차 AP는 이미 6이다(32장 가 안 적용). 실제 기준으로 다시 비교
if "--real" in sys.argv:
    go("현재(실제: 1차 AP 6)", [], 6, 2)
    go("마: 1차 AP 5, 2차 AP 3", ["A4", "A8", "C3", "N2"], 5, 3)
    go("마: 1차 AP 4, 2차 AP 3", ["A4", "A8", "C3", "N2"], 4, 3)
