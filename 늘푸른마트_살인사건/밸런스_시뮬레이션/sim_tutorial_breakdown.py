import random, sys
from collections import defaultdict, Counter
sys.stdout.reconfigure(encoding="utf-8")
import sim_tutorial as s
R = s.R; SJ, JM, CY, OH = R
random.seed(5); n = 20000
contrib = defaultdict(float); pos_top = Counter(); neg_only = defaultdict(float)
for _ in range(n):
    x = s.run(policy="strategic")
    k = {c for c in x["known"] if c in s.S1}
    pos = {r: 0.0 for r in R}
    for c in k:
        for r, w in s.S1[c][2].items():
            contrib[(r, c)] += w / n
            if w > 0: pos[r] += w
            else: neg_only[r] += w / n
    for a, b, r, w in [("A2", "K2", JM, 1), ("A2", "K4", OH, 1), ("A7", "N1", JM, .5)]:
        if {a, b} <= k:
            contrib[(r, a + "+" + b)] += w / n; pos[r] += w
    mx = max(pos.values()); t = [r for r in R if pos[r] == mx]
    for r in t: pos_top[r] += 1 / len(t)
for r in R:
    items = sorted(((c, v) for (rr, c), v in contrib.items() if rr == r), key=lambda z: -abs(z[1]))
    print(r, " / ".join(f"{c} {v:+.2f}" for c, v in items[:8]))
print("혐의만(알리바이 빼고) 1차 끝 1위:", {r: f"{pos_top[r]/n*100:.0f}%" for r in R})
print("알리바이로 깎인 평균:", {r: round(neg_only[r], 2) for r in R})
