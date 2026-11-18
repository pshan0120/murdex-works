"""2026-11-18 유나슈퍼 단서 추가 뒤 최유나 쏠림 완화안 비교 (sim_tutorial.py 정본, 무게 ±20%)

가: 뒷골목#2의 옛 간판을 뺀다(수첩 표지 "유나슈퍼"만 남김). 이 자리가 유나슈퍼였다는 건 최유나가 털어놓거나 역할지 밖 추리로만.
나: 서지훈 역할지의 "우리 아빠 그렇게 만들어 놓고"를 "무슨 말인지는 잘 들리지 않았다" 쪽으로 흐린다(증언 무게 1.0 → 0.5).
다: 최유나 증언에 "2시 37분 기사가 카운터 뒤 사무실 쪽을 자꾸 들여다봤다"를 더한다(정민재 +0.4). 역할지 사실과 맞다.
"""
import random, sys, copy
from collections import Counter
sys.stdout.reconfigure(encoding="utf-8")
import sim_tutorial as s
SJ, JM, CY, OH = s.R
B2, BT = copy.deepcopy(s.S2), list(s.TESTI)
ORIG = s.pressure
OPT = {}


def patched(k, stage, variant, said, jit):
    p = ORIG(k, stage, variant, said, jit)
    if stage == 2 and OPT.get("no_sign") and {"M1", "D1"} <= k:
        p[CY] -= .3
    if OPT.get("elim") and {"A2", "A6"} <= k:
        for r in (SJ, CY, OH): p[r] -= .8
    return p


s.pressure = patched


def reset():
    s.S2.clear(); s.S2.update(copy.deepcopy(B2)); s.TESTI[:] = list(BT); OPT.clear()


def set_testi(prefix, w):
    for i, t in enumerate(s.TESTI):
        if t[4].startswith(prefix):
            s.TESTI[i] = (t[0], t[1], w, t[3], t[4])


def go(name, n=20000):
    out = []
    for elim in (False, True):
        OPT["elim"] = elim
        random.seed(5)
        res = [s.run(policy="strategic", noise=.2) for _ in range(n)]
        a = [x for x in res if x["action"]]
        out.append((s.top_rates(res, "p1"), s.top_rates(res, "p2"), s.top_rates(a, "p2")[JM] / len(a)))
    f = lambda t: " ".join(f"{r} {t[r]/n*100:.0f}%" for r in s.R)
    print(f"[{name}]\n  1차 끝: {f(out[0][0])}\n  2차 끝: {f(out[0][1])}\n  소거 추리 해냄 2차 끝: {f(out[1][1])} | 액션 쓴 판 정민재 {out[1][2]*100:.0f}%")


reset(); go("현재")
reset(); s.S2["M1"] = (None, True, {CY: .5}); OPT["no_sign"] = 1; go("가: 옛 간판 삭제")
reset(); set_testi("서지훈: 지난주", .5); go("나: 서지훈이 들은 말 흐리기")
reset(); s.TESTI.append((CY, JM, .4, 1, "최유나: 기사가 사무실 쪽을 들여다봤다")); go("다: 정민재가 사무실을 들여다봄")
reset(); set_testi("서지훈: 지난주", .5); s.TESTI.append((CY, JM, .4, 1, "최유나: 기사가 사무실 쪽을 들여다봤다")); go("나 + 다")
reset(); s.S2["M1"] = (None, True, {CY: .5}); OPT["no_sign"] = 1; s.TESTI.append((CY, JM, .4, 1, "최유나: 기사가 사무실 쪽을 들여다봤다")); go("가 + 다")
