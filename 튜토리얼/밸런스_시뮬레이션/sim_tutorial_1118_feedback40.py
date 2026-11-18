"""2026-11-18 테스트 40차 단서 수정 반영 비교 (sim_tutorial.py 정본, 무게 ±20%)

반영한 것
- 카운터#2(C1) 매출장부 수입 칸 "한빛 20,000,000 (예정)": 한빛물류는 정민재 공개 정보라 한 장으로도 정민재에게 이어진다(+.4).
  통장 매달 100만 원(C3)과 합치면 돈을 받아 온 관계가 드러난다(+.4).
- 오하린에 대하여#1(K4) 회색 양말: 실밥(E1) 후보가 넷이 된다(오하린 +.15, 양말이 손잡이에 닿기는 어려워 셋보다 약하게).
- 오하린에 대하여#3(S2) 사망보험금 1억 원 표시: 1.4 → 1.7.
- 서지훈 POS 지침 보강: 전략적 방침에서 서지훈이 1차에 카운터#1을 먼저 조사하는 확률 80%가 그대로 유효하다는 근거. 무게 변화 없음.
- 입구 우산꽂이(시작 단계): 시뮬레이션은 "정민재만 젖어 있다"는 의심을 원래 넣지 않았다. 실제 플레이의 쏠림을 줄이는 수정이라 무게 변화 없음.
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
    if OPT.get("new") and {"C1", "C3"} <= k:
        p[JM] += .4
    if OPT.get("elim") and {"A2", "A6"} <= k:
        for r in (SJ, CY, OH): p[r] -= .8
    return p


s.pressure = patched


def reset():
    s.S1.clear(); s.S1.update(copy.deepcopy(B1)); s.S2.clear(); s.S2.update(copy.deepcopy(B2)); OPT.clear()


def apply_new():
    s.S1["C1"] = (None, True, {OH: .3, JM: .4})
    s.S2["E1"] = (None, True, {JM: .2, SJ: .2, CY: .2, OH: .15})
    s.S2["S2"] = ("NOT:" + OH, False, {OH: 1.7})
    OPT["new"] = 1


def go(name, n=20000):
    out = []
    keep = dict(OPT)
    for elim in (False, True):
        OPT.clear(); OPT.update(keep); OPT["elim"] = elim
        random.seed(5)
        res = [s.run(policy="strategic", noise=.2) for _ in range(n)]
        a = [x for x in res if x["action"]]
        out.append((s.top_rates(res, "p1"), s.top_rates(res, "p2"), s.top_rates(a, "p2")[JM] / len(a), s.top_rates(a, "p2")))
    f = lambda t, m=n: " ".join(f"{r} {t[r]/m*100:.0f}%" for r in s.R)
    print(f"[{name}]\n  1차 끝: {f(out[0][0])}\n  2차 끝: {f(out[0][1])}\n  소거 추리 해냄 2차 끝: {f(out[1][1])}"
          f"\n  액션 쓴 판 정민재: 압박만 {out[0][2]*100:.0f}% / 소거 추리 {out[1][2]*100:.0f}%")


reset(); go("현재(40차 수정 전)")
reset(); apply_new(); go("40차 단서 수정 후")


# 나: 장부에 이름 없이 "20,000,000 (예정)"만. 한 장으로는 누구 돈인지 모른다(정민재 +.1).
#     정민재 통화 목록의 02:16 통화(N1) 또는 통장 매달 100만 원(C3)과 합쳐야 정민재로 이어진다(각 +.3).
def apply_na():
    apply_new()
    s.S1["C1"] = (None, True, {OH: .3, JM: .1})
    OPT["new"] = 0
    OPT["na"] = 1


_P = s.pressure
def patched_na(k, stage, variant, said, jit):
    p = _P(k, stage, variant, said, jit)
    if OPT.get("na"):
        if {"C1", "C3"} <= k: p[JM] += .3
        if stage == 2 and {"C1", "N1"} <= k: p[JM] += .3
    return p
s.pressure = patched_na

reset(); apply_na(); go("나: 이름 없이 금액만")
