import random, sys
sys.stdout.reconfigure(encoding="utf-8")
import sim_tutorial as s
from sim_tutorial_variants import quick, reset, move
SJ, JM, CY, OH = s.R
orig = s.pressure
def patched(k, stage, variant=False):
    p = orig(k, stage, variant)
    if PATCH.get("a7") and {"A7", "N1"} <= k: p[JM] += 1.2
    return p
s.pressure = patched; PATCH = {}
print("\n=== 알리바이 단서를 2차로 미루는 안 ===")
reset(); move("S1", "L3"); move("S2", "L4")
quick("최유나 영수증↔메신저, 오하린 사진첩↔메모")
quick("  같은 안, 무게 ±40%", noise=.4)
s.S1["A7"] = ("ONLY:" + OH, True, {SJ: 1, JM: .3}); PATCH["a7"] = 1
quick("  + 점주 휴대폰 통화 상대를 번호로만")
quick("  + 같은 안, 무게 ±40%", noise=.4)
s.S1["C3"] = (None, True, {JM: .8}); s.S2["N2"] = ("NOT:" + JM, False, {JM: 1.3})
quick("  + 서랍은 전표 사본만(통장은 지갑 명세표로)")
quick("  + 같은 안, 무게 ±40%", noise=.4)
