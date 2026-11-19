"""2026-11-18 1차 조사 AP 5 → 6 비교 (미적용, sim_tutorial.py 정본 위에서)

테스트 플레이에서 1차가 끝날 때 단서 3장(POS, 오하린#1·#2)이 남았고, 2차에 그 3장을 2차 AP로 여느라
2차 단서 넷(○○에 대하여#3)을 못 봤다. 정본 시뮬레이션은 1차에 못 본 단서가 2차로 넘어가지 않는다고 가정했으므로,
여기서는 '이월'을 넣는다: 1차에 남은 단서도 2차에 조사할 수 있고 2차 AP를 쓴다.

비교: 1차 AP 5(현재) / 6(가 안), 이월 없음(정본 가정) / 이월 있음(실제 플레이).
조사 순서: 현재 sim의 pick(전략적 정책: 서지훈 POS·오하린 휴대폰을 80% 먼저) 그대로.
"""
import random, sys, statistics as st
from collections import Counter, defaultdict
sys.stdout.reconfigure(encoding="utf-8")
import sim_tutorial as s
SJ, JM, CY, OH = s.R
R = s.R


def run(ap1=5, ap2=2, carry=True, action_p=.8, noise=.2, policy="strategic"):
    known, hidden, holder, hand = set(), set(), {}, defaultdict(list)
    jit = defaultdict(lambda: random.uniform(1 - noise, 1 + noise)) if noise else None
    S12 = {**s.S1, **s.S2}

    def investigate(pool, stage, ap):
        apl = {r: ap for r in R}
        used_action = False
        for _ in range(ap + 2):
            order = R[:]; random.shuffle(order)
            for r in order:
                if apl[r] <= 0:
                    continue
                if stage == 2 and r == JM and not used_action and "F3" not in holder and random.random() < action_p:
                    used_action = True; apl[r] -= 1; continue
                avail = [c for c in pool if c not in holder and s.can(c, r, S12)]
                if not avail:
                    continue
                c = s.pick(r, avail, policy, 1 if c_in_s1(avail) else stage)
                holder[c] = r; hand[r].append(c); apl[r] -= 1
        return used_action, sum(apl.values())

    def c_in_s1(avail):
        return any(c in s.S1 for c in avail)

    def share(codes):
        for c in codes:
            if c not in holder:
                continue
            r = holder[c]
            if S12[c][1]:
                known.add(c)
            elif S12[c][2].get(r, 0) > 0 and random.random() < (s.HIDE_SELF_P_CULPRIT if r == s.CULPRIT else s.HIDE_SELF_P):
                hidden.add(c)
            else:
                known.add(c)

    said = {"front": True}
    said.update({i: True for i in range(len(s.TESTI))})
    _, left1 = investigate(list(s.S1), 1, ap1)
    share(s.S1)
    unfound1 = [c for c in s.S1 if c not in holder]
    p1 = s.pressure(known, 1, False, said, jit)
    pool2 = list(s.S2) + (unfound1 if carry else [])
    action, left2 = investigate(pool2, 2, ap2)
    share(S12)
    p2 = s.pressure(known, 2, action, said, jit)
    unfound2 = [c for c in S12 if c not in holder]
    elim = {"A2", "A6"} <= known
    return dict(p1=p1, p2=p2, unfound1=unfound1, unfound2=unfound2, action=action, elim=elim, left1=left1, left2=left2)


def report(name, n=20000, **kw):
    random.seed(11)
    res = [run(**kw) for _ in range(n)]
    t1, t2 = s.top_rates(res, "p1"), s.top_rates(res, "p2")
    # 소거 추리를 해낸 경우(바닥+도어락이 나오고 안쪽 셋을 지움)
    el = []
    for x in res:
        p = dict(x["p2"])
        if x["elim"]:
            for r in (SJ, CY, OH): p[r] -= .8
        el.append({"p2": p, "action": x["action"]})
    te = s.top_rates(el, "p2")
    a = [x for x in el if x["action"]]
    ta = s.top_rates(a, "p2")[JM] / max(1, len(a))
    f = lambda t: " ".join(f"{r} {t[r]/n*100:.0f}%" for r in R)
    m1 = st.mean(len(x["unfound1"]) for x in res); m2 = st.mean(len(x["unfound2"]) for x in res)
    z1 = sum(not x["unfound1"] for x in res) / n; z2 = sum(not x["unfound2"] for x in res) / n
    u2 = Counter(c for x in res for c in x["unfound2"])
    print(f"\n[{name}]")
    print(f"  1차 끝 못 본 단서 평균 {m1:.2f}장(다 본 판 {z1*100:.0f}%) | 끝까지 못 본 단서 평균 {m2:.2f}장(다 본 판 {z2*100:.0f}%)")
    print(f"  1차 남은 AP 평균 {st.mean(x['left1'] for x in res):.2f} | 2차 남은 AP 평균 {st.mean(x['left2'] for x in res):.2f}")
    print(f"  끝까지 못 본 단서 많은 순: {[(c, f'{v/n*100:.0f}%') for c, v in u2.most_common(5)]}")
    print(f"  1차 끝 1위: {f(t1)}")
    print(f"  2차 끝 1위: {f(t2)}")
    print(f"  소거 추리 해냄 2차 끝: {f(te)} | 액션 쓴 판 정민재 {ta*100:.0f}%")


if __name__ == "__main__":
    report("현재: 1차 5AP, 이월 없음(정본 가정)", ap1=5, carry=False)
    report("현재: 1차 5AP, 이월 있음(실제 플레이)", ap1=5, carry=True)
    report("가: 1차 6AP, 이월 있음", ap1=6, carry=True)
    report("현재: 1차 5AP, 이월 있음, 아무렇게나 조사(독점 단서를 먼저 챙기지 않음)", ap1=5, carry=True, policy="random")
    report("가: 1차 6AP, 이월 있음, 아무렇게나 조사", ap1=6, carry=True, policy="random")
    report("참고: 1차 5AP + 2차 3AP, 이월 있음, 아무렇게나 조사", ap1=5, ap2=3, carry=True, policy="random")
    report("참고: 1차 6AP + 2차 3AP, 이월 있음, 아무렇게나 조사", ap1=6, ap2=3, carry=True, policy="random")
