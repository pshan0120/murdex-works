"""(2026-11-17 정본, 같은 날 자기 불리 단서 숨김 기준 반영) 늘푸른마트 살인사건 역할별 밸런스 시뮬레이션 (나를 좋아하는 사람에게 sim_narul.py 방식).

단서마다 역할별 압박 무게를 붙이고, 조사 판을 수만 번 무작위로 돌려
테이블에 나온 단서 + 역할지 속 증언으로 역할별 압박을 센다.

2026-11-17 반영:
- 창고#4·#5 합침(A5 삭제) → 1차 20장/AP 20
- 오하린#3 사진첩 촬영 시각 삭제 → 사진 알리바이 없음. 오하린은 바닥 자국과 정문 목격으로 빠진다
- 카운터#2 PC 화면에 실제 매출·대부 이자, 카운터#5 서류철에 매출표 4,500만 원 → 오하린 동기 짝
- 최유나#2 메신저에 수진 01:58 메시지 → 수첩과 짝
- 트럭: 목장갑·운전석 발판 자국 삭제 → 법원 봉투 + 블랙박스만
- 회색 실밥 후보: 정민재(작업복), 서지훈(티셔츠), 최유나(짙은 회색 카디건)
- 목장갑 설정 삭제(실밥은 정민재 작업복 소매). 서지훈의 "늘 목장갑을 낀다"도 삭제
- 공유(2026-11-17 같은 날 기준 변경, 사용자 지정): 찾은 단서는 기본적으로 공개한다. 찾은 사람 자신에게 불리한
  단서(그 역할 무게 > 0)는 숨긴다(0.8, 범인 0.9). 장소 단서는 조사 즉시 전원 공개라 숨길 수 없고,
  인물 단서는 본인이 못 집으므로 자연히 공개된다. 남의 알리바이를 숨긴다는 옛 가정(EXCULPATE)은 참고 실행에만 쓴다.
- 정문 목격 증언(최유나·서지훈)은 늘 나온다
- 신발 젖음·마름 묘사 삭제(고무장화도 후보), 서류철의 보험증권 내용 삭제(사진첩 2차로만)
이전 정본은 sim_tutorial_2026-11-15.py.
"""
import random, sys, statistics as st
from collections import Counter, defaultdict
sys.stdout.reconfigure(encoding="utf-8")

R = ["서지훈", "정민재", "최유나", "오하린"]
SJ, JM, CY, OH = R
CULPRIT = JM

# code: (조사 가능 제한: None=누구나, "ONLY:역할", "NOT:역할"), 장소(전원 공개) 여부, 압박{역할:무게}
S1 = {
    # 창고 (공개)
    "A1": (None, True, {}), "A2": (None, True, {}), "A3": (None, True, {}),
    "A4": (None, True, {JM: .3}),                        # 담배 상자 + 전표(합침)
    "A6": (None, True, {SJ: .3, JM: .3, OH: .3}),        # 도어락 02:00/02:10/02:22/02:24
    "A7": ("ONLY:" + OH, True, {JM: .3, SJ: 1}),         # 02:16 통화 번호 가림, 서지은 문자
    "A8": (None, True, {}),
    # 카운터 (공개)
    "B1": ("ONLY:" + SJ, True, {SJ: -.4, CY: -.5}),
    "C1": (None, True, {OH: .3}),                        # PC 02:18 로그인 + 실제 매출·대부 이자
    "C4": (None, True, {SJ: 1.5}), "C3": (None, True, {JM: .8}), "C5": (None, True, {OH: 1.3}),  # 계약서+매출표+보험회사 봉투(증권 내용 삭제)
    # 인물 (본인 제외, 소유)
    "K1": ("NOT:" + SJ, False, {SJ: .1}), "L1": ("NOT:" + SJ, False, {SJ: 1.5}),
    "N2": ("NOT:" + JM, False, {JM: .4}), "K2": ("NOT:" + JM, False, {JM: .3}),
    "D1": ("NOT:" + CY, False, {CY: 1.8}), "L3": ("NOT:" + CY, False, {CY: 1.8}),   # 수진 메시지 추가 1.5→1.8
    "K4": ("NOT:" + OH, False, {OH: .3}), "L4": ("NOT:" + OH, False, {OH: 1.5}),
}
S2 = {
    "E1": (None, True, {JM: .2, SJ: .2, CY: .2}),        # 회색 실밥: 회색 옷 셋
    "G1": (None, True, {SJ: .5}),
    "F3": (None, True, {JM: 1.0}),                       # 법원 봉투 + 블랙박스 (목장갑·발판 삭제)
    "M1": (None, True, {CY: .5}),
    "L2": ("NOT:" + SJ, False, {SJ: 1.5}), "N1": ("NOT:" + JM, False, {JM: 1}),
    "S1": ("NOT:" + CY, False, {CY: .9}),                # 영수증 -0.3 + 메모 +1.2
    "S2": ("NOT:" + OH, False, {OH: 1.4}),               # 촬영 시각 없음, 보험증권(수익자·계약일)은 여기서만
}
F3_VARIANT = {JM: .4}                                    # 액션 뒤: 법원 봉투 + 켜지지 않는 블랙박스(2026-11-17 빈 슬롯 삭제)
assert len(S1) == 20 and len(S2) == 8
EXCULPATE = {"B1", "S1"}  # 남의 혐의를 벗겨 주는 단서(범인이 쥐면 숨길 수 있음)

# 역할지 속 증언: (말하는 사람, 대상, 무게, 꺼낼 확률, 설명)
TESTI = [
    # 2026-11-17 숨길 이유가 없는 증언은 항상 나온다(역할_밸런스_분석_방법.md 3장). 옛 확률 .7/.6/.5
    (SJ, CY, 1.0, 1, "서지훈: 지난주 최유나가 점주에게 '가만두지 않을 거예요'"),
    (CY, OH, .5, 1, "최유나: 오하린이 1시 50분에 와서 점주와 다툼"),
    (CY, SJ, -.3, 1, "최유나: 서지훈은 계속 카운터에 있었다"),
    (None, SJ, .3, 1, "공지 사실: 서지훈이 시신 첫 발견"),
]
FRONT_P = 1.0  # 최유나·서지훈이 "2시 20분쯤 담배 손님 말고 정문 드나든 사람 없다"를 꺼낼 확률


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


HIDE_SELF_P, HIDE_SELF_P_CULPRIT = .8, .9


def run(policy="random", action_p=.8, hide_p=0, share_p=1.0, ap1=5, ap2=2, noise=0.0, hide_self=1.0):
    known = set()
    hidden = set()
    holder = {}
    hand = defaultdict(list)
    jit = defaultdict(lambda: random.uniform(1 - noise, 1 + noise)) if noise else None

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
            r = holder[c]
            if table[c][1]:
                known.add(c)
            elif table[c][2].get(r, 0) > 0 and random.random() < (HIDE_SELF_P_CULPRIT if r == CULPRIT else HIDE_SELF_P) * hide_self:
                hidden.add(c)
            elif r == CULPRIT and c in EXCULPATE and random.random() < hide_p:
                pass
            elif random.random() < share_p:
                known.add(c)

    said = {"front": random.random() < FRONT_P}
    said.update({i: random.random() < t[3] for i, t in enumerate(TESTI)})

    investigate(S1, 1, ap1)
    share(S1)
    p1 = pressure(known, 1, False, said, jit)
    unfound1 = [c for c in S1 if c not in holder]
    action = investigate(S2, 2, ap2)
    share(S2)
    p2 = pressure(known, 2, action, said, jit)
    unfound2 = [c for c in S2 if c not in holder]
    k = known
    floor = {"A2", "A3", "K2"} <= k                         # 걸레질 뒤 격자무늬 = 정민재 안전화(오하린 레인부츠와 갈라야 함)
    door = {"A2", "A6"} <= k and said["front"]              # 뒷문으로만 오감 + 정문 드나든 사람 없음 → 바깥 사람
    truck = "F3" in k and "A6" in k and not action          # 블랙박스 02:21·02:25가 도어락 02:22·02:24 앞뒤
    return dict(p1=p1, p2=p2, unfound1=unfound1, unfound2=unfound2, action=action,
                floor=floor, door=door, truck=truck,
                held={r: len(hand[r]) for r in R}, known=set(k), hidden=set(hidden))


def pressure(k, stage, variant, said, jit):
    p = {r: 0.0 for r in R}
    J = (lambda key: jit[key]) if jit is not None else (lambda key: 1.0)
    tables = [S1] + ([S2] if stage == 2 else [])
    for t in tables:
        for c in t:
            if c in k:
                w = F3_VARIANT if (c == "F3" and variant) else t[c][2]
                for r, v in w.items():
                    p[r] += v * J(c)

    def add(r, v, key):
        p[r] += v * J(key)
    # 조합 (1차)
    floor = 1 if "A3" in k else .5
    # 2026-11-17 신발 젖음·마름 묘사 삭제, 고무장화는 누구나 신을 수 있음 → 신발 짝 약하게
    if {"A2", "K2"} <= k: add(JM, .6 * floor, "A2K2")
    if {"A2", "K4"} <= k: add(OH, .6 * floor, "A2K4")
    if {"A2", "K1"} <= k: add(SJ, .2, "A2K1")
    if {"C3", "N2"} <= k: add(JM, .7, "C3N2")
    if {"D1", "L4"} <= k: add(CY, .5, "D1L4")     # "뒷문 15"와 "1507"
    if {"D1", "A6"} <= k: add(CY, .2, "D1A6")
    if {"D1", "L3"} <= k: add(CY, .5, "D1L3")     # 수진 "그 사람" + 수첩 "늘푸른마트 뒤 계단"
    if {"C1", "C5"} <= k: add(OH, .8, "C1C5")     # 매출표 4,500만 vs 실제 2,480만 + 대부 이자
    # 정문 목격: 바닥(매장 쪽 문에서 시작한 격자무늬 없음)과 도어락이 나오면 안쪽 사람이 빠진다
    if said["front"] and {"A2", "A6"} <= k:
        add(OH, -.8, "front_OH"); add(CY, -.4, "front_CY"); add(SJ, -.4, "front_SJ")
    if stage == 2:
        if {"A7", "N1"} <= k: add(JM, 1.2, "A7N1")
        if {"B1", "S1"} <= k: add(CY, -.8, "B1S1")
        if {"S1", "A3"} <= k: add(CY, .3, "S1A3")
        if {"S2", "C5"} <= k: add(OH, .3, "S2C5")  # 봉투와 사진
        if {"S2", "L4"} <= k: add(OH, .3, "S2L4")  # 메모의 보험 서류 위치
        if {"G1", "L2"} <= k: add(SJ, .5, "G1L2")
        if {"M1", "D1"} <= k: add(CY, .5, "M1D1")
        if {"F3", "A6"} <= k and not variant: add(JM, .6, "F3A6")
    for i, (who, tgt, w, pr, _) in enumerate(TESTI):
        if said[i]:
            add(tgt, w, f"T{i}")
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
    second = Counter(); close = 0
    for x in res:
        p = x["p2"]; o = sorted(((v, r) for r, v in p.items() if r != JM), reverse=True)
        second[o[0][1]] += 1
        if p[JM] - o[0][0] < 1.0: close += 1
    print("범인 다음으로 의심받는 사람(2차 끝): " + " ".join(f"{r} {second[r]/n*100:.0f}%" for r in R if r != JM)
          + f" | 정민재와 차이 1점 미만 {close/n*100:.0f}%")
    u1 = Counter(c for x in res for c in x["unfound1"])
    u2 = Counter(c for x in res for c in x["unfound2"])
    print("1차 못 본 단서:", [(c, f"{v/n*100:.0f}%") for c, v in u1.most_common(6)])
    print("2차 못 본 단서:", [(c, f"{v/n*100:.0f}%") for c, v in u2.most_common(6)])
    h = Counter(c for x in res for c in x["hidden"])
    print("끝까지 숨겨진 단서:", [(c, f"{v/n*100:.0f}%") for c, v in h.most_common(6)])
    print(f"블랙박스 액션 사용 {sum(x['action'] for x in res)/n*100:.0f}%")
    f = sum(x["floor"] for x in res) / n; d = sum(x["door"] for x in res) / n; t = sum(x["truck"] for x in res) / n
    anyp = sum(x["floor"] or x["door"] or x["truck"] for x in res) / n
    two = sum((x["floor"] + x["door"] + x["truck"]) >= 2 for x in res) / n
    print(f"풀이 경로: 바닥·신발 {f*100:.0f}% / 출입(도어락+정문) {d*100:.0f}% / 블랙박스 {t*100:.0f}% | 하나 이상 {anyp*100:.0f}% | 둘 이상 {two*100:.0f}%")
    return res


if __name__ == "__main__":
    random.seed(17)
    report("완전 랜덤", policy="random")
    report("전략적(서지훈 POS·오하린 휴대폰 먼저)", policy="strategic")
    report("전략적, 무게 ±20%", policy="strategic", noise=.2)
    report("전략적, 무게 ±40%", policy="strategic", noise=.4)
    report("참고: 아무도 숨기지 않음(18~19장 가정)", policy="strategic", hide_self=0)
    report("참고: 옛 공유 가정(인물 단서 90% 공개, 범인이 남의 알리바이 60% 숨김)", policy="strategic", hide_p=.6, share_p=.9)
    report("범인이 액션을 안 씀", policy="strategic", action_p=0)
