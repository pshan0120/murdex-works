import random, sys
sys.stdout.reconfigure(encoding="utf-8")
import sim_tutorial as s
from sim_tutorial_variants import quick, reset, move
SJ, JM, CY, OH = s.R
orig = s.pressure
def patched(k, stage, variant=False):
    p = orig(k, stage, variant)
    if {"A7", "N1"} <= k: p[JM] += 1.2
    return p
s.pressure = patched
print("\n=== 정민재 통화 목록까지 2차로 ===")
reset(); move("S1", "L3"); move("S2", "L4"); move("N1", "N2")
s.S1["A7"] = ("ONLY:" + OH, True, {SJ: 1, JM: .3})
quick("알리바이 2장 2차로 + 통화 상대 번호만 + 통화 목록↔지갑")
quick("  무게 ±40%", noise=.4)
