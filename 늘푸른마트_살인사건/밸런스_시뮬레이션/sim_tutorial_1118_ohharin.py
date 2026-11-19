"""2026-11-18 오하린 2차 의심 보강안 비교 (sim_tutorial.py 정본 기준, 무게 ±20%)

가: 최유나 증언 "1시 50분에 사무실로 들어간 그 여자를 그 뒤로 보지 못했다"(창가에서 사무실 안은 안 보임). 오하린이 사무실에 있었다는 걸 본 사람이 없다.
나: 오하린#3 사진첩에 지난주 금요일 찍은 창고 뒷문 도어락 사진. 휴대폰 메모 "뒷문 1507"과 짝.
다: 카운터#6(사무실 CCTV 녹화기, 2차)에 "책상 서랍이 열려 있고 서류철이 흐트러져 있다". 누군가 사무실을 뒤졌다. 사진첩과 짝.
"""
import random, sys, copy
from collections import Counter
sys.stdout.reconfigure(encoding="utf-8")
import sim_tutorial as s
SJ, JM, CY, OH = s.R
B1, B2, BT = copy.deepcopy(s.S1), copy.deepcopy(s.S2), list(s.TESTI)
ORIG = s.pressure
OPT = {}


def patched(k, stage, variant, said, jit):
    p = ORIG(k, stage, variant, said, jit)
    if stage == 2:
        if OPT.get("door_photo") and {"S2", "L4"} <= k: p[OH] += .3
        if OPT.get("office") and {"G1", "S2"} <= k: p[OH] += .2
    if OPT.get("elim") and {"A2", "A6"} <= k:
        for r in (SJ, CY, OH): p[r] -= .8
    return p


s.pressure = patched


def reset():
    s.S1.clear(); s.S1.update(copy.deepcopy(B1)); s.S2.clear(); s.S2.update(copy.deepcopy(B2))
    s.TESTI[:] = list(BT); OPT.clear()


def go(name, n=20000):
    rows = []
    for elim in (False, True):
        OPT["elim"] = elim
        random.seed(5)
        res = [s.run(policy="strategic", noise=.2) for _ in range(n)]
        rows.append((s.top_rates(res, "p1"), s.top_rates(res, "p2")))
    f = lambda t: " ".join(f"{r} {t[r]/n*100:.0f}%" for r in s.R)
    print(f"[{name}]\n  1차 끝: {f(rows[0][0])}\n  2차 끝: {f(rows[0][1])}\n  소거 추리 해냄 2차 끝: {f(rows[1][1])}")


def opt_ga():
    s.TESTI.append((CY, OH, .3, 1, "최유나: 1시 50분 뒤로 그 여자를 다시 보지 못했다"))


def opt_na():
    s.S2["S2"] = ("NOT:" + OH, False, {OH: 1.8}); OPT["door_photo"] = 1


def opt_da():
    s.S2["G1"] = (None, True, {SJ: .5, OH: .3}); OPT["office"] = 1


reset(); go("현재")
reset(); opt_ga(); go("가: 최유나 '그 뒤로 못 봤다'")
reset(); opt_na(); go("나: 사진첩에 뒷문 도어락 사진")
reset(); opt_da(); go("다: 사무실 서랍이 뒤져진 흔적")
reset(); opt_ga(); opt_na(); go("가 + 나")
reset(); opt_ga(); opt_da(); go("가 + 다")
