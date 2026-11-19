"""2026-11-17 민감도: 정문 목격 증언이 나오는 비율, 오하린 동기 짝 무게"""
import random, sys
sys.stdout.reconfigure(encoding="utf-8")
import sim_tutorial as s
SJ, JM, CY, OH = s.R

def go(name, n=20000, **kw):
    random.seed(5)
    res = [s.run(policy="strategic", **kw) for _ in range(n)]
    t1, t2 = s.top_rates(res, "p1"), s.top_rates(res, "p2")
    print(f"[{name}] 1차 끝: " + " ".join(f"{r} {t1[r]/n*100:.0f}%" for r in s.R)
          + " | 2차 끝: " + " ".join(f"{r} {t2[r]/n*100:.0f}%" for r in s.R))

for fp in (.3, .5, .8, 1.0):
    s.FRONT_P = fp
    go(f"정문 증언 {int(fp*100)}%")
s.FRONT_P = .5
orig = s.pressure
def no_oh_combo(k, stage, variant, said, jit):
    p = orig(k, stage, variant, said, jit)
    if {"C1", "C5"} <= k: p[OH] -= .8
    return p
s.pressure = no_oh_combo
go("참고: 매출표·대부 이자 짝 없음(어제 전 오하린 동기)")
s.pressure = orig
s.S2["S2"] = ("NOT:" + OH, False, {OH: .6})
go("참고: 사진 촬영 시각이 남아 있다면(사진첩 +0.6)")
