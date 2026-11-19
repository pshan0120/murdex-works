"""2026-11-18 최유나가 2차 끝에 거의 빠지는 문제 대응안 비교 (sim_tutorial.py 정본 기준, 무게 ±20%)

가: 영수증을 빼고 카디건 소매의 풀린 회색 실밥으로 바꾼다. 커피 알리바이는 서지훈 기억 + POS로만(카드 끝자리로 잇지 않음).
나: 영수증은 두고, 최유나#3에 카디건 소매의 풀린 회색 실밥을 더한다.
다: 영수증 시각·카드 끝자리를 모두 지워 "아메리카노 1"만 남긴다. 서지훈 기억 + POS로 이어야 알리바이가 선다.
"""
import random, sys, copy
from collections import Counter
sys.stdout.reconfigure(encoding="utf-8")
import sim_tutorial as s
SJ, JM, CY, OH = s.R
B2 = copy.deepcopy(s.S2); B1 = copy.deepcopy(s.S1); ORIG = s.pressure; OPT = {}


def patched(k, stage, variant, said, jit):
    p = ORIG(k, stage, variant, said, jit)
    if stage == 2:
        if OPT.get("no_receipt_link") and {"B1", "S1"} <= k:
            p[CY] += .8                       # 카드 끝자리 짝 삭제
        if OPT.get("sj_memory") and "B1" in k:
            p[CY] -= .6                       # 서지훈 "몇 분 뒤 최유나가 아메리카노" + POS 02:24
        if OPT.get("thread") and {"S1", "E1"} <= k:
            p[CY] += .6                       # 소화기 실밥과 카디건 소매
    if OPT.get("elim") and {"A2", "A6"} <= k:
        for r in (SJ, CY, OH):
            p[r] -= .8
    return p


s.pressure = patched


def reset():
    s.S2.clear(); s.S2.update(copy.deepcopy(B2)); s.S1.clear(); s.S1.update(copy.deepcopy(B1)); OPT.clear()


def go(name, n=20000):
    out = []
    for elim in (False, True):
        OPT["elim"] = elim
        random.seed(5)
        res = [s.run(policy="strategic", noise=.2) for _ in range(n)]
        t1, t2 = s.top_rates(res, "p1"), s.top_rates(res, "p2")
        sec = Counter()
        for x in res:
            o = sorted(((v, r) for r, v in x["p2"].items() if r != JM), reverse=True); sec[o[0][1]] += 1
        out.append((t1, t2, sec))
    (t1, t2, sec), (_, t2e, _) = out
    f = lambda t: " ".join(f"{r} {t[r]/n*100:.0f}%" for r in s.R)
    print(f"[{name}]\n  1차 끝: {f(t1)}\n  2차 끝: {f(t2)}\n  소거 추리 해냄 2차 끝: {f(t2e)}\n  범인 다음: " + " ".join(f"{r} {sec[r]/n*100:.0f}%" for r in s.R if r != JM))


reset(); go("현재")
reset(); s.S2["S1"] = ("NOT:" + CY, False, {CY: 1.5}); s.S1["B1"] = ("ONLY:" + SJ, True, {SJ: -.4})
OPT.update(no_receipt_link=1, sj_memory=1, thread=1); go("가: 영수증 → 카디건 실밥, 알리바이는 서지훈 기억+POS")
reset(); s.S2["S1"] = ("NOT:" + CY, False, {CY: 1.2}); OPT.update(thread=1); go("나: 영수증 두고 카디건 실밥 추가")
reset(); s.S2["S1"] = ("NOT:" + CY, False, {CY: 1.2}); s.S1["B1"] = ("ONLY:" + SJ, True, {SJ: -.4})
OPT.update(no_receipt_link=1, sj_memory=1); go("다: 영수증은 '아메리카노 1'만, 알리바이는 서지훈 기억+POS")
reset(); s.S2["S1"] = ("NOT:" + CY, False, {CY: 1.2}); s.S1["B1"] = ("ONLY:" + SJ, True, {SJ: -.4})
OPT.update(no_receipt_link=1, sj_memory=1, thread=1); go("다 + 카디건 실밥")
