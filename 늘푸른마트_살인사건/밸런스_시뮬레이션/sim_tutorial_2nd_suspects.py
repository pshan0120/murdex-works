"""2026-11-15 2차 조사에 최유나·오하린 의심 거리 더하는 안 비교"""
import random, sys, copy
sys.stdout.reconfigure(encoding="utf-8")
import sim_tutorial as s
SJ, JM, CY, OH = s.R
B1, B2 = copy.deepcopy(s.S1), copy.deepcopy(s.S2)
orig = s.pressure
EX = {}
def patched(k, stage, variant=False):
    p = orig(k, stage, variant)
    if stage == 2:
        if EX.get("ins") and {"S2", "C5"} <= k: p[OH] += .3
        if EX.get("memo") and {"S1", "A3"} <= k: p[CY] += .3   # 창고 청소 시각과 맞물림
        if EX.get("gray") and "E1" in k: p[CY] += .3
    return p
s.pressure = patched
def go(name, n=20000):
    random.seed(3)
    res = [s.run(policy="strategic") for _ in range(n)]
    t1, t2 = s.top_rates(res, "p1"), s.top_rates(res, "p2")
    two = sum((x["phys"] + x["alibi"] + x["truck"]) >= 2 for x in res) / n
    print(f"[{name}]\n  1차 끝: " + " ".join(f"{r} {t1[r]/n*100:.0f}%" for r in s.R) +
          "\n  2차 끝: " + " ".join(f"{r} {t2[r]/n*100:.0f}%" for r in s.R) + f"  (풀이 경로 둘 이상 {two*100:.0f}%)")
def reset():
    s.S1.clear(); s.S1.update(copy.deepcopy(B1)); s.S2.clear(); s.S2.update(copy.deepcopy(B2)); EX.clear()
go("현재(적용 전 기준이던 줄, 지금은 적용 후 정본)")
reset(); s.S2["S1"] = ("NOT:" + CY, False, {CY: .9}); EX["memo"] = 1
go("최유나 안1: 영수증 옆 메모 '화·금 2시 납품, 끝나면 혼자 창고 청소'")
reset(); s.S2["S2"] = ("NOT:" + OH, False, {OH: .6}); EX["ins"] = 1
go("오하린 안1: 사진첩 맨 앞에 02:17 보험증권 사진")
reset(); s.S2["S1"] = ("NOT:" + CY, False, {CY: .9}); EX["memo"] = 1; s.S2["S2"] = ("NOT:" + OH, False, {OH: .6}); EX["ins"] = 1
go("최유나 안1 + 오하린 안1")
EX["gray"] = 1
go("  + 최유나 안2: 티셔츠를 회색으로(냉장고 실밥 후보)")

def margin(name, n=20000):
    random.seed(3)
    res = [s.run(policy="strategic") for _ in range(n)]
    close = 0; second = {r: 0 for r in s.R}
    for x in res:
        p = x["p2"]; jm = p[JM]; others = sorted(((v, r) for r, v in p.items() if r != JM), reverse=True)
        if jm - others[0][0] < 1.0: close += 1
        second[others[0][1]] += 1
    print(f"[{name}] 2차 끝 정민재와 다음 사람 차이 1점 미만 {close/n*100:.0f}% | 범인 다음으로 의심받는 사람: " +
          " ".join(f"{r} {v/n*100:.0f}%" for r, v in second.items() if r != JM))
print()
reset(); margin("현재")
s.S2["S1"] = ("NOT:" + CY, False, {CY: .9}); EX["memo"] = 1; s.S2["S2"] = ("NOT:" + OH, False, {OH: .6}); EX["ins"] = 1
margin("최유나 안1 + 오하린 안1")
s.S2["S1"] = ("NOT:" + CY, False, {CY: 2.0}); s.S2["S2"] = ("NOT:" + OH, False, {OH: 2.0})
go("참고: 두 단서를 트럭만큼 무겁게(+2.0)"); margin("참고: 두 단서를 트럭만큼 무겁게(+2.0)")
