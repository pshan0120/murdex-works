"""2026-11-26 장소 단서 소유 가정의 두 번째 실행: 숨기는 기준을 바꿔 본다.
기준 A(정본): 자기 무게 > 0이면 숨김. 도어락·실밥처럼 여럿을 함께 가리키는 단서까지 숨겨 너무 비관적이다.
기준 B: 자기를 가장 무겁게 가리키는 단서만 숨김(자기 무게 > 0이고 다른 누구보다 크다).
"""
import sys, types, random
from collections import Counter
sys.stdout.reconfigure(encoding="utf-8")
src = open("sim_tutorial.py", encoding="utf-8").read()
src = src.replace('if __name__ == "__main__":', 'if False:')
old = "elif table[c][2].get(r, 0) > 0 and random.random()"
assert old in src
src = src.replace(old, "elif hide_rule(table[c][2], r) and random.random()")
src = src.replace("def run(", "RULE='A'\ndef hide_rule(w, r):\n    me = w.get(r, 0)\n    if me <= 0: return False\n    if RULE == 'A': return True\n    return all(me > v for k, v in w.items() if k != r)\n\ndef run(", 1)
s = types.ModuleType("simx"); exec(compile(src, "simx", "exec"), s.__dict__)
SJ, JM, CY, OH = s.R
ORIG_P = s.pressure; OPT = {}
def patched(k, stage, variant, said, jit):
    p = ORIG_P(k, stage, variant, said, jit)
    if OPT.get("elim") and {"A2", "A6"} <= k:
        for r in (SJ, OH): p[r] -= .8
        if "B1" in k: p[CY] -= .8
    return p
s.pressure = patched
O1, O2 = dict(s.S1), dict(s.S2)
def set_owned(owned):
    for src_, dst in ((O1, s.S1), (O2, s.S2)):
        for c, (lim, pub, w) in src_.items(): dst[c] = (lim, pub and not owned, w)
n = 20000
f = lambda t: " / ".join(f"{t[r]/n*100:.0f}" for r in s.R)
for owned, rule, name in ((False, "A", "지금(즉시 공개)"), (True, "A", "소유 + 자기에게 불리하면 숨김"), (True, "B", "소유 + 자기를 가장 무겁게 가리킬 때만 숨김")):
    set_owned(owned); s.RULE = rule
    print(f"\n#### {name} ####")
    for elim in (False, True):
        OPT["elim"] = elim; random.seed(5)
        res = [s.run(policy="strategic", noise=.2) for _ in range(n)]
        print(f"{'소거 추리 해냄' if elim else '압박만'}: 1차 끝 {f(s.top_rates(res,'p1'))} | 2차 끝 {f(s.top_rates(res,'p2'))}")
    h = Counter(c for x in res for c in x["hidden"])
    print("숨겨진 단서:", ", ".join(f"{c} {v/n*100:.0f}%" for c, v in h.most_common(10)))
    print(f"풀이 경로 하나 이상 {sum(x['floor'] or x['door'] or x['truck'] for x in res)/n*100:.0f}% (바닥 {sum(x['floor'] for x in res)/n*100:.0f} / 출입 {sum(x['door'] for x in res)/n*100:.0f} / 블랙박스 {sum(x['truck'] for x in res)/n*100:.0f})")
