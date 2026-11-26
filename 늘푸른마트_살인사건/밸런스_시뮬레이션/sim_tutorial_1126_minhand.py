"""2026-11-26 사용자 제안: 장소 단서도 소유로 바꾸고 최소 보유 단서 1장(min_hand_limit=1).
가정(사용자 지정): 범인이 아닌 사람은 찾은 단서를 적극 공개한다. 범인은 자기에게 불리한 단서를 숨긴다(0.9).
최소 보유 1장은 보드 공개와 건네주기만 막는다(reveal_clue_to_board_use_case, respond_clue_exchange_use_case).
함께보기와 말로 알리기는 그대로 된다. 그래서 무고한 사람이 손에 남긴 1장은 말이나 함께보기로 알릴 확률 V로 둔다.
남길 1장은 자기에게 가장 불리한 단서를 고른다고 본다.
"""
import random, sys
from collections import Counter, defaultdict
sys.stdout.reconfigure(encoding="utf-8")
import sim_tutorial as s
R = s.R; SJ, JM, CY, OH = R; CUL = s.CULPRIT

def run(owned, min_hand, V, culprit_hide=.9, ap1=5, ap2=3, action_p=.8, noise=.2, elim=False):
    jit = defaultdict(lambda: random.uniform(1 - noise, 1 + noise))
    holder, hand, known, hidden = {}, defaultdict(list), set(), set()
    def table_pub(t, c): return t[c][1] and not owned
    def investigate(t, stage, ap):
        apl = {r: ap for r in R}; used = False
        for _ in range(ap):
            o = R[:]; random.shuffle(o)
            for r in o:
                if apl[r] <= 0: continue
                if stage == 2 and r == JM and not used and "F3" not in holder and random.random() < action_p:
                    used = True; apl[r] -= 1; continue
                av = [c for c in t if c not in holder and s.can(c, r, t)]
                if not av: continue
                c = s.pick(r, av, "strategic", stage)
                holder[c] = r; hand[r].append(c); apl[r] -= 1
        return used
    def share(t):
        for r in R:
            mine = [c for c in hand[r] if c in t]
            pub = [c for c in mine if table_pub(t, c)]
            known.update(pub)
            priv = [c for c in mine if c not in pub]
            if r == CUL:
                for c in priv:
                    if t[c][2].get(r, 0) > 0 and random.random() < culprit_hide: hidden.add(c)
                    else: known.add(c)
                continue
            # 무고한 사람: 손에 남은 카드(이번까지 보드에 안 올린 것) 중 min_hand장은 남긴다
            in_hand = [c for c in hand[r] if c not in known and c not in hidden and not any(c in tt and table_pub(tt, c) for tt in (s.S1, s.S2))]
            keep = []
            if min_hand:
                # 이미 앞 단계에서 남겨 둔 카드가 있으면 그걸로 채운다
                kept_before = [c for c in hand[r] if c in kept[r]]
                need = max(0, min_hand - len(kept_before))
                cand = sorted(priv, key=lambda c: -t[c][2].get(r, 0))
                keep = cand[:need]; kept[r].update(keep)
            for c in priv:
                if c in keep:
                    (known.add(c) if random.random() < V else hidden.add(c))
                else:
                    known.add(c)
    kept = defaultdict(set)
    said = {"front": True}; said.update({i: True for i in range(len(s.TESTI))})
    investigate(s.S1, 1, ap1); share(s.S1)
    p1 = s.pressure(known, 1, False, said, jit)
    act = investigate(s.S2, 2, ap2); share(s.S2)
    p2 = s.pressure(known, 2, act, said, jit)
    if elim and {"A2", "A6"} <= known:
        for r in (SJ, OH): p2[r] -= .8
        if "B1" in known: p2[CY] -= .8
    paths = ({"A2","A3","K2"} <= known) or ({"A2","A6"} <= known) or ("F3" in known and "A6" in known and not act)
    return dict(p1=p1, p2=p2, hidden=hidden, paths=paths)

n = 20000
f = lambda t: " / ".join(f"{t[r]/n*100:.0f}" for r in R)
CASES = [
    ("지금(장소 즉시 공개), 무고한 사람 전부 공개", False, 0, 1),
    ("장소 소유, 무고한 사람 전부 공개, 최소 보유 없음", True, 0, 1),
    ("장소 소유 + 최소 1장, 남긴 1장도 말·함께보기로 알림(V=.8)", True, 1, .8),
    ("장소 소유 + 최소 1장, 남긴 1장은 안 알림(V=0, 가장 나쁜 경우)", True, 1, 0),
]
for name, owned, mh, V in CASES:
    out = []
    for elim in (False, True):
        random.seed(5)
        res = [run(owned, mh, V, elim=elim) for _ in range(n)]
        out.append(res)
    h = Counter(c for x in out[0] for c in x["hidden"])
    print(f"\n#### {name} ####")
    print(f"1차 끝 {f(s.top_rates(out[0],'p1'))} | 2차 끝 {f(s.top_rates(out[0],'p2'))} | 소거 추리 2차 끝 {f(s.top_rates(out[1],'p2'))} | 풀이 경로 {sum(x['paths'] for x in out[0])/n*100:.0f}%")
    print("숨겨진 단서:", ", ".join(f"{c} {v/n*100:.0f}%" for c, v in h.most_common(8)))
