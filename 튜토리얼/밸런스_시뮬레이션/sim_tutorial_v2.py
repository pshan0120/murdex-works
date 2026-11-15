import random, sys, copy
sys.stdout.reconfigure(encoding="utf-8")
import sim_tutorial as s
from sim_tutorial_variants import quick, reset, move
SJ, JM, CY, OH = s.R
orig_pressure = s.pressure
EXTRA = {}
def patched(k, stage, variant=False):
    p = orig_pressure(k, stage, variant)
    if EXTRA.get("a7n1") and {"A7", "N1"} <= k: p[JM] += EXTRA["a7n1"]
    if EXTRA.get("x1d1") and {"X1", "D1"} <= k: p[CY] += .5
    return p
s.pressure = patched
print("\n=== 설계안 ===")
reset(); EXTRA.clear()
# 안1: 점주 휴대폰 통화 상대를 번호로만(정민재 통화 목록과 맞춰야 누구인지 드러남)
s.S1["A7"] = ("ONLY:" + OH, True, {SJ: 1, JM: .3}); EXTRA["a7n1"] = 1.2
quick("안1: 점주 휴대폰 통화 상대를 번호로만")
# 안2: 책상 서랍에서 통장을 빼 전표 사본만(통장 입금 내역은 2차 지갑 명세표 쪽으로)
s.S1["C3"] = (None, True, {JM: .8}); s.S2["N2"] = ("NOT:" + JM, False, {JM: 1.3})
quick("안1+안2: 서랍은 전표 사본만")
reset(); EXTRA.clear()
s.S1["A7"] = ("ONLY:" + OH, True, {SJ: 1, JM: .3}); EXTRA["a7n1"] = 1.2
# 안3: 담배 상자(A5)를 전표(A4)와 합치고, 빈 자리에 최유나 쪽 공개 단서(점주 책상 메모 등)
del s.S1["A5"]; s.S1["X1"] = (None, True, {CY: 1}); EXTRA["x1d1"] = 1
quick("안1+안3: 최유나 쪽 공개 단서 추가(A4·A5 합침)")
s.S1["C3"] = (None, True, {JM: .8}); s.S2["N2"] = ("NOT:" + JM, False, {JM: 1.3})
quick("안1+안2+안3")
quick("안1+안2+안3, 무게 ±40%", noise=.4)
