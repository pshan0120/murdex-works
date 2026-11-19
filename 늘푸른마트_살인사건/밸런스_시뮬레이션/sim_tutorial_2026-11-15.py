"""(2026-11-15 안 ② 적용 정본) 늘푸른마트 살인사건 역할별 밸런스 시뮬레이션 (나를 좋아하는 사람에게 sim_narul.py 방식).

단서마다 역할별 압박 무게를 붙이고, 조사 판을 수만 번 무작위로 돌려
테이블에 나온 단서 + 역할지 속 증언으로 역할별 압박을 센다.
"""
import random, sys, statistics as st
from collections import Counter, defaultdict
sys.stdout.reconfigure(encoding="utf-8")

R = ["서지훈", "정민재", "최유나", "오하린"]
SJ, JM, CY, OH = R
CULPRIT = JM

# code: (조사 가능 제한: None=본인 외 누구나/장소, "ONLY:역할", "NOT:역할"), 공개 여부, 압박{역할:무게}
S1 = {
    # 창고 (공개)
    "A1": (None, True, {}), "A2": (None, True, {}), "A3": (None, True, {}),
    "A4": (None, True, {JM: .3}), "A5": (None, True, {}),
    "A6": (None, True, {SJ: .3, JM: .3, OH: .3}),
    "A7": ("ONLY:" + OH, True, {JM: .3, SJ: 1}),  # 02:16 통화 상대는 번호만(2026-11-15)
    "A8": (None, True, {}),
    # 카운터 (공개)
    "B1": ("ONLY:" + SJ, True, {SJ: -.4, CY: -.5}),  # B1: 02:19와 02:24 사이 5분(2026-11-15)
    "C1": (None, True, {OH: -.3}),
    "C4": (None, True, {SJ: 1.5}), "C3": (None, True, {JM: .8}), "C5": (None, True, {OH: 1.9}),  # C3: 통장 보낸 사람 이름 없음(2026-11-15)
    # 인물 (본인 제외, 소유)
    "K1": ("NOT:" + SJ, False, {SJ: .2}), "L1": ("NOT:" + SJ, False, {SJ: 1.5}),
    "N2": ("NOT:" + JM, False, {JM: .4}), "K2": ("NOT:" + JM, False, {JM: .5}),
    "D1": ("NOT:" + CY, False, {CY: 1.8}), "L3": ("NOT:" + CY, False, {CY: 1.5}),
    "K4": ("NOT:" + OH, False, {OH: .5}), "L4": ("NOT:" + OH, False, {OH: 1.5}),
}
S2 = {
    "E1": (None, True, {JM: .3, SJ: .2}), "G1": (None, True, {SJ: .5}),
    "F3": (None, True, {JM: 1.6}), "M1": (None, True, {CY: .5}),
    "L2": ("NOT:" + SJ, False, {SJ: 1.5}), "N1": ("NOT:" + JM, False, {JM: 1}),
    "S1": ("NOT:" + CY, False, {CY: .9}), "S2": ("NOT:" + OH, False, {OH: .6}),  # 영수증 -0.3+메모 +1.2 / 사진 알리바이 -0.6+02:17 보험증권 +1.2
}
F3_VARIANT = {JM: 1.1}
assert len(S1) == 21 and len(S2) == 8
EXCULPATE = {"B1", "C1", "S1", "S2"}  # 남의 혐의를 벗겨 주는 단서

# 역할지 속 증언: (말하는 사람, 대상, 무게, 꺼낼 확률, 설명)
TESTI = [
    (SJ, CY, 1.0, .7, "서지훈: 지난주 최유나가 점주에게 '가만두지 않을 거예요'"),
    (CY, OH, .5, .6, "최유나: 오하린이 1시 50분에 와서 점주와 다툼"),
    (CY, SJ, -.3, .5, "최유나: 서지훈은 계속 카운터에 있었다"),
    (None, SJ, .3, 1, "공지 사실: 서지훈이 시신 첫 발견"),
]


def can(code, r, table):
    own = table[code][0]
    if own is None:
        return True
    kind, who = own.split(":")
    return (r == who) if kind == "ONLY" else (r != who)


def pick(r, avail, policy, stage):
    if policy == "strategic":
        if stage == 1 and r == SJ and "B1" in avail and random.random() < .8:
            return "B1"
        if stage == 1 and r == OH and "A7" in avail and random.random() < .8:
            return "A7"
    return random.choice(avail)


def run(policy="random", action_p=.8, hide_p=.6, ap1=5, ap2=2):
    known = set()
    holder = {}
    hand = defaultdict(list)

    def investigate(table, stage, ap):
        apl = {r: ap for r in R}
        used_action = False
        for _ in range(ap):
            order = R[:]
            random.shuffle(order)
            for r in order:
                if apl[r] <= 0:
                    continue
                if stage == 2 and r == JM and not used_action and "F3" not in holder and random.random() < action_p:
                    used_action = True; apl[r] -= 1; continue
                avail = [c for c in table if c not in holder and can(c, r, table)]
                if not avail:
                    continue
                c = pick(r, avail, policy, stage)
                holder[c] = r; hand[r].append(c); apl[r] -= 1
        return used_action

    def share(table):
        for c in table:
            if c not in holder:
                continue
            pub = table[c][1]
            r = holder[c]
            if pub:
                known.add(c)
            elif r == CULPRIT and c in EXCULPATE and random.random() < hide_p:
                pass  # 범인은 남의 혐의를 벗겨 주는 단서를 숨긴다
            elif random.random() < .9:
                known.add(c)

    investigate(S1, 1, ap1)
    share(S1)
    p1 = pressure(known, stage=1)
    unfound1 = [c for c in S1 if c not in holder]
    action = investigate(S2, 2, ap2)
    share(S2)
    p2 = pressure(known, stage=2, variant=action)
    unfound2 = [c for c in S2 if c not in holder]
    k = known
    phys = {"A2", "A3", "K2", "S2"} <= k
    alibi = {"A6", "B1", "S2"} <= k
    truck = "F3" in k and ("E1" in k or {"A2", "A3"} <= k)
    return dict(p1=p1, p2=p2, unfound1=unfound1, unfound2=unfound2, action=action,
                phys=phys, alibi=alibi, truck=truck,
                held={r: len(hand[r]) for r in R}, known=set(k))


def pressure(k, stage, variant=False):
    p = {r: 0.0 for r in R}
    tables = [S1] + ([S2] if stage == 2 else [])
    for t in tables:
        for c in t:
            if c in k:
                w = F3_VARIANT if (c == "F3" and variant) else t[c][2]
                for r, v in w.items():
                    p[r] += v
    # 조합
    floor = 1 if "A3" in k else .5
    if {"A2", "K2"} <= k: p[JM] += 1 * floor
    if {"A2", "K4"} <= k: p[OH] += 1 * floor
    if {"A2", "K1"} <= k: p[SJ] += .2
    if {"C3", "N2"} <= k: p[JM] += .7  # 날짜, 금액이 맞음
    if {"D1", "L4"} <= k: p[CY] += .5  # "뒷문 15"와 "1507"
    if {"D1", "A6"} <= k: p[CY] += .2  # 뒷문을 열 수 있었을지도
    if stage == 2:
        if {"A7", "N1"} <= k: p[JM] += 1.2
        if {"B1", "S1"} <= k: p[CY] -= .8  # 카드 끝자리로 02:24가 맞춰짐
        if {"S1", "A3"} <= k: p[CY] += .3  # 메모와 청소 점검표 02:12
        if {"S2", "C5"} <= k: p[OH] += .3  # 보험증권 사진과 서류철
        if {"S2", "C1"} <= k: p[OH] -= .5
        if {"G1", "L2"} <= k: p[SJ] += .5
        if {"M1", "D1"} <= k: p[CY] += .5
        if {"F3", "E1"} <= k: p[JM] += .4
        if {"F3", "A6"} <= k and not variant: p[JM] += .6  # 움직임 감지가 도어락 앞뒤
        if {"F3", "A2"} <= k: p[JM] += .5
    # 증언
    for who, tgt, w, pr, _ in TESTI:
        if random.random() < pr:
            p[tgt] += w
    if "S2" not in k and random.random() < .5:  # 오하린이 사진첩을 먼저 털어놓음
        p[OH] -= .5
    return p


def top_rates(res, key):
    top = Counter()
    for x in res:
        mx = max(x[key].values())
        t = [r for r in R if x[key][r] == mx]
        for r in t:
            top[r] += 1 / len(t)
    return top


def report(name, n=20000, **kw):
    res = [run(**kw) for _ in range(n)]
    t1, t2 = top_rates(res, "p1"), top_rates(res, "p2")
    print(f"\n######## {name} (n={n}) ########")
    print("역할 | 압박 1차 끝 | 1위 비율 1차 | 압박 2차 끝 | 1위 비율 2차 | 보유 단서")
    for r in R:
        print(f"{r} | {st.mean(x['p1'][r] for x in res):.2f} | {t1[r]/n*100:.0f}% | "
              f"{st.mean(x['p2'][r] for x in res):.2f} | {t2[r]/n*100:.0f}% | {st.mean(x['held'][r] for x in res):.2f}")
    u1 = Counter(c for x in res for c in x["unfound1"])
    u2 = Counter(c for x in res for c in x["unfound2"])
    print("1차 못 본 단서:", [(c, f"{v/n*100:.0f}%") for c, v in u1.most_common(6)])
    print("2차 못 본 단서:", [(c, f"{v/n*100:.0f}%") for c, v in u2.most_common(6)])
    print(f"블랙박스 액션 사용 {sum(x['action'] for x in res)/n*100:.0f}%")
    ph = sum(x["phys"] for x in res) / n; al = sum(x["alibi"] for x in res) / n; tr = sum(x["truck"] for x in res) / n
    anyp = sum(x["phys"] or x["alibi"] or x["truck"] for x in res) / n
    two = sum((x["phys"] + x["alibi"] + x["truck"]) >= 2 for x in res) / n
    none_p1 = sum(not (x["phys"] or x["alibi"]) for x in res) / n
    print(f"풀이 경로: 신발 {ph*100:.0f}% / 알리바이 {al*100:.0f}% / 트럭 {tr*100:.0f}% | 하나 이상 {anyp*100:.0f}% | 둘 이상 {two*100:.0f}%")
    print(f"1차 단서만으로 풀이 경로(신발·알리바이) 없음 {none_p1*100:.0f}%")
    s2 = sum("S2" in x["known"] for x in res) / n
    print(f"오하린 사진첩(S2) 테이블에 나옴 {s2*100:.0f}%  (범인이 들고 숨긴 비율 "
          f"{sum(('S2' not in x['known']) for x in res)/n*100:.0f}% 중 일부)")
    return res


if __name__ == "__main__":
    random.seed(11)
    report("완전 랜덤", policy="random")
    report("전략적(서지훈 POS·오하린 휴대폰 먼저)", policy="strategic")
    report("범인이 숨기지 않음", policy="strategic", hide_p=0)
    report("범인이 액션을 안 씀", policy="strategic", action_p=0)
