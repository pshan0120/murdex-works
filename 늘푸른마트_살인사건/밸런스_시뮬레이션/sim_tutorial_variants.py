import random, sys, copy
from collections import Counter
sys.stdout.reconfigure(encoding="utf-8")
import sim_tutorial as s
SJ, JM, CY, OH = s.R
BASE1, BASE2 = copy.deepcopy(s.S1), copy.deepcopy(s.S2)


def move(a, b):
    """1차 단서 a와 2차 단서 b의 단계를 맞바꾼다"""
    s.S2[a] = s.S1.pop(a)
    s.S1[b] = s.S2.pop(b)


def quick(name, n=20000, noise=0.0, **kw):
    random.seed(3)
    orig = {}
    res = []
    for _ in range(n):
        if noise:  # 단서 무게를 판마다 ±noise 비율로 흔든다(무게를 내가 정한 것이라 민감도 확인)
            for t in (s.S1, s.S2):
                for c, (o, pub, w) in list(t.items()):
                    orig.setdefault((id(t), c), w)
                    t[c] = (o, pub, {r: v * random.uniform(1 - noise, 1 + noise) for r, v in orig[(id(t), c)].items()})
        res.append(s.run(policy="strategic", **kw))
    t1, t2 = s.top_rates(res, "p1"), s.top_rates(res, "p2")
    two = sum((x["phys"] + x["alibi"] + x["truck"]) >= 2 for x in res) / n
    anyp = sum(x["phys"] or x["alibi"] or x["truck"] for x in res) / n
    print(f"[{name}]")
    print("  1차 끝 1위: " + " ".join(f"{r} {t1[r]/n*100:.0f}%" for r in s.R) +
          " | 2차 끝 1위: " + " ".join(f"{r} {t2[r]/n*100:.0f}%" for r in s.R))
    print(f"  풀이 경로 하나 이상 {anyp*100:.0f}%, 둘 이상 {two*100:.0f}%")
    if noise:
        for t in (s.S1, s.S2):
            for c, (o, pub, w) in list(t.items()):
                t[c] = (o, pub, orig[(id(t), c)])


def reset():
    s.S1.clear(); s.S1.update(copy.deepcopy(BASE1))
    s.S2.clear(); s.S2.update(copy.deepcopy(BASE2))


quick("현재")
quick("현재, 무게 ±40% 흔들기", noise=.4)
move("S1", "L3"); quick("최유나: 메신저를 1차로, 영수증을 2차로")
reset(); move("N1", "N2"); quick("정민재: 통화 목록을 2차로, 지갑을 1차로")
move("S1", "L3"); quick("둘 다")
quick("둘 다, 무게 ±40% 흔들기", noise=.4)
