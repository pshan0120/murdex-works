"""#나를_좋아하는_사람에게 역할 밸런스 시뮬레이션 (2026-11-17, 같은 날 자기 불리 단서 숨김·엿보기 반영, D2·G2 약하게 조정, N10 추가, 옥상 열린 창 추가. 이전 정본 sim_narul_2026-11-17c.py)

방법: works/역할_밸런스_분석_방법.md
템플릿: works/역할_밸런스_시뮬레이션_템플릿.py 를 바탕으로, 이 작품에 필요한 것을 덧붙였다.
  - 공개 단서(AP 0, 단계 시작에 전원 공개)
  - 잠긴 단서(비밀번호를 풀어야 열림, 푼 확률과 풀 수 있는 역할)
  - AP만 쓰는 행동(엿보기, 경찰 신고)
  - 단계마다 바뀌는 무게(조사 2단계에서 창밖 투척이 드러나면 2층 안의 흔적은 힘이 빠지고, 바깥·뒤쪽 창 흔적은 힘이 세진다)
  - 게시판에서 찾는 사실(AP 없음, 찾을 확률)
  - 소거 추리의 "또는" 조건

실행: python sim_narul.py
"""
import random, sys, statistics as st
from collections import Counter, defaultdict
sys.stdout.reconfigure(encoding="utf-8")

# =====================================================================
# 작품별 설정
# =====================================================================
PH, JH, YJ, NH, JJ = "박혜수", "정형미", "유정석", "노형철", "정준희"
ROLES = [PH, JH, YJ, NH, JJ]
CULPRIT = JH

# 조사 단계: (이름, 인당 AP). 조사 2단계(옥상)는 전체 공개 단서만 있다. 장면 3은 조사 2단계와 3단계 사이.
STAGES = [("조사 1단계", 9), ("조사 2단계", 0), ("조사 3단계", 3)]   # 장면 3(허리띠, 채찍)은 조사 3단계 결과에 들어간다

# 단서: 코드 -> (단계, 조사 제한, 공개 단서 여부, {역할: 무게})
#   조사 제한: None / "NOT:역할"("○○에 대하여" 묶음은 본인 조사 불가) / "W"(잠긴 단서, LOCKS 참고)
CLUES = {
    # ---- 조사 1단계: 공개
    "A1": (0, None, True, {}),           # 시신(외형은 박혜수와 닮음, 오살 추리 재료)
    "D4": (0, None, True, {}),           # 층별 안내(진행 단서)
    # ---- 조사 1단계: 장소·사물
    "A2": (0, None, False, {PH: .5}),    # 창틀 꽁초(범행 시각)
    "A3": (0, None, False, {YJ: 1.0}),   # 하도훈 PC(익명7315, 재입장)
    "A5": (0, None, False, {PH: 1.0}),   # 하도훈 휴대폰 18:20 수신
    "A6": (0, None, False, {PH: 1.0}),   # 등과 손목 자국(채찍 미끼)
    "B1": (0, None, False, {}), "B2": (0, None, False, {}), "B4": (0, None, False, {}),
    "C1": (0, None, False, {}),
    "C2": (0, None, False, {JJ: .5}),    # 창업 멤버 사진(정태호 생김새)
    "D1": (0, None, False, {NH: 1.5}),   # 회의실 창문 + 창틀 초록 페인트
    "D2": (0, None, False, {JH: .7, PH: .3}),   # 재떨이 꽁초 2개(2026-11-17 점검표 삭제, 1.5→0.7)
    "D3": (0, None, False, {JJ: 1.0}),   # 1층 여자화장실 창문
    "E1": (0, None, False, {PH: 1.5}),   # 2층 여자화장실 세면대
    "E2": (0, None, False, {}),          # 케이크
    "G6": (0, None, False, {PH: .5}),    # 하도훈 17:50 퇴근, 경비원 저녁
    "G7": (0, None, False, {PH: .5}),    # 퇴근 뒤 2층 불
    "G8": (0, None, False, {}), "G9": (0, None, False, {}),
    # ---- 조사 1단계: ○○에 대하여
    "H1": (0, "NOT:" + PH, False, {PH: 1.5}),
    "W1": (0, "W", False, {PH: 2.0}),
    "J1": (0, "NOT:" + JH, False, {JH: 2.0}),
    "G2": (0, "NOT:" + JH, False, {JH: .7}),   # 2026-11-17 "한 시간도 안" 삭제, 1.5→0.7
    "A15": (0, "NOT:" + JH, False, {JH: 1.0}),
    "W2": (0, "W", False, {JH: 2.0}),
    "P7": (0, "NOT:" + YJ, False, {YJ: .5}),   # 통화 3분(20:04에 끝남)
    "A7": (0, "NOT:" + YJ, False, {YJ: 1.0}),
    "A10": (0, "NOT:" + YJ, False, {YJ: 1.5}),
    "A13": (0, "NOT:" + YJ, False, {YJ: .5}),  # 화분(둔기 미끼)
    "G3": (0, "NOT:" + YJ, False, {YJ: .3}),
    "W3": (0, "W", False, {YJ: 1.0}),
    "A9": (0, "NOT:" + NH, False, {NH: 1.0}),
    "A12": (0, "NOT:" + NH, False, {NH: .5}),  # 텀블러(둔기 미끼)
    "G4": (0, "NOT:" + NH, False, {NH: 1.0}),
    "H2": (0, "NOT:" + NH, False, {NH: 1.5}),  # 팔꿈치 페인트
    "W4": (0, "W", False, {NH: 1.5}),
    "A8": (0, "NOT:" + JJ, False, {JJ: 1.5}),
    "A11": (0, "NOT:" + JJ, False, {JJ: 1.0}), # 공구상자(둔기 미끼)
    "B6": (0, "NOT:" + JJ, False, {JJ: 1.0}),
    "G5": (0, "NOT:" + JJ, False, {JJ: 1.0}),
    "W5": (0, "W", False, {JJ: 1.5}),
    # ---- 조사 2단계(옥상): 전부 공개
    "R-1": (1, None, True, {}), "R-2": (1, None, True, {}), "R-3": (1, None, True, {}), "R-4": (1, None, True, {}),
    # ---- 조사 3단계
    "M6": (2, None, False, {}), "N1": (2, None, False, {}), "N2": (2, None, False, {}), "N3": (2, None, False, {}),
    "N4": (2, None, False, {}), "N5": (2, None, False, {}),
    "M3": (2, None, False, {PH: .3}),
    "N6": (2, None, False, {YJ: .5}),    # 한결안전관리 대표 유희철
    "M1": (2, None, False, {JH: 1.5}),   # 소방수, 희철이 곁에 둔 한 사람
    "N7": (2, None, False, {PH: .5}),    # "박 실장에게 말함"
    "M2": (2, None, False, {YJ: .3}),
    "N8": (2, None, False, {}),
    "N10": (2, None, False, {NH: 1.0}),  # 여문혁의 일지 한 장: 하도훈이 여문혁 서랍을 뒤짐(2026-11-17 추가)
    "M9": (2, None, True, {}), "M8": (2, None, True, {}),
}

# 단계별 무게 배수: 조사 2단계에서 창밖 투척(R-1)이 드러난 뒤의 해석 변화
STAGE_MULT = {
    1: {"H1": .4, "E1": .4, "A5": .6, "A2": .5, "G6": .5, "G7": .5,
        "A11": 0, "A12": 0, "A13": 0,
        "H2": 1.4, "D1": 1.4, "D3": 1.4, "J1": 1.5, "G2": 1.3, "D2": 1.3},
}
STAGE_MULT[2] = STAGE_MULT[1]

# 잠긴 단서: 코드 -> (조사 1단계 안에 번호를 풀 확률, 풀 수 있는 역할)
LOCKS = {
    "W1": (.45, [JH, YJ, NH, JJ]),   # 실마리 "2003 영업본부 워크숍" -> 게시판 R4
    "W2": (.35, [PH, YJ, NH, JJ]),   # "은사님" -> R29, R14/R16, R1/R2
    "W3": (.35, [PH, JH, NH, JJ]),   # 케이크 스티커 -> R7(유희철 득남)
    "W4": (.55, [YJ, JJ]),           # "팀장님 것" -> T1(사료관리팀 전용)
    "W5": (.30, [PH, JH, YJ, NH]),   # "아빠" -> 정태호 -> R1/R2, R4
}

# 숨김(2026-11-17 사용자 지정): 찾은 사람 자신에게 불리한 단서(그 역할 무게 > 0)는 숨길 가능성이 높다.
#   "○○에 대하여"는 본인이 못 집으므로 자연히 공개된다. 이 작품에는 조사 즉시 전원 공개되는 단서가 없다.
HIDE_SELF_P = .8
HIDE_SELF_P_CULPRIT = .9
# 엿보기(어깨너머로 보기): (역할들, 단계, 쓸 확률). AP 1, 남이 숨긴 단서 하나를 보고 PEEK_SHARE_P로 공개.
PEEKS = [([PH, JH, YJ, NH, JJ], 0, .8)]
PEEK_SHARE_P = .8

# AP만 쓰는 행동: (역할들, 단계, 쓸 확률)
AP_SINKS = [
    ([YJ], 0, .5), ([NH], 0, .5), ([JJ], 0, .5),  # 경찰 신고
]

# 게시판에서 찾는 사실: (이름, 대상, 무게, 찾을 확률, 적용 시작 단계)
BOARD = [
    ("R8·R9·R29 정형미의 던지기 이력과 장학생", JH, .5, .7, 1),
    ("R14·R16 유희철이 조직문화팀 초대 팀장", JH, .3, .7, 2),   # M1과 합쳐질 때 뜻이 선다(짝에서 셈)
    ("R25 익명7315 뒷담화", YJ, .3, .8, 0),
]

# 단서 짝: (필요 단서 집합, 역할, 무게, 이 단계부터)
COMBOS = [
    ({"A5", "W1"}, PH, 1.0, 0),          # 18:20 통화
    ({"H1", "E1"}, PH, .5, 0),
    ({"A3", "A10"}, YJ, .5, 0),          # 7315 = 하도훈, 유정석이 알고 있었음
    ({"D1", "H2"}, NH, .5, 0),           # 창틀 페인트와 팔꿈치
    ({"R-1", "G3"}, YJ, .3, 1),          # 하필 자기 차
    ({"A1", "A2", "R-1"}, JH, .3, 1),    # 창가의 사람을 박혜수로 착각했을 수 있다
    ({"J1"}, JH, 1.0, 2),                # 장면 3: 허리띠 쓸린 자국 + 마스크 자국
    ({"M1", "BOARD:R14·R16 유희철이 조직문화팀 초대 팀장"}, JH, 1.0, 2),
    ({"W3", "N6"}, YJ, .5, 2),           # 아버지가 한결안전관리 대표
    ({"D3"}, JJ, .5, 1),                 # 열린 창이 화장실 창이라는 것을 D3로 맞춤(2026-11-17)
    ({"N10", "A9"}, NH, .5, 2),          # 하도훈이 수첩과 노형철 서랍을 캐고 다님
    ({"N10", "W4"}, NH, .5, 2),          # 수첩이 지금 노형철 서랍에 있음
]

# 역할지 속 증언·공지 사실: (말하는 역할 또는 None, 대상, 무게, 꺼낼 확률, 필요 단서, 적용 시작 단계, 설명)
TESTIMONY = [
    (JH, PH, 1.0, .8, set(), 0, "정형미: 박혜수가 흡연구역에 없었다(왜 찾았는지 되물을 수 있어 0.8)"),
    (None, PH, .3, 1.0, set(), 0, "공지: 박혜수 19:55 '담배' 외출"),
    (None, JH, .3, 1.0, set(), 0, "공지: 정형미 20:00 '담배' 외출"),
    (None, NH, .5, 1.0, set(), 0, "공지: 20:00~20:08 회의실에 노형철 혼자"),
    (None, JJ, .3, 1.0, set(), 0, "공지: 정준희 시신 첫 발견"),
    (JJ, YJ, .5, 1.0, set(), 0, "정준희: 돌아올 때 계단 쪽이 비어 있었다"),
    (YJ, JH, .8, 1.0, {"D2"}, 0, "유정석: 18:36 정형미와 둘이 피웠다 + D2 꽁초 두 개 → 20:00 담배는 거짓"),
    (YJ, PH, .3, 1.0, {"D2"}, 0, "같은 짝: 박혜수의 19:55 담배도 거짓"),
    (JJ, YJ, 1.0, 1.0, {"P7"}, 0, "정준희 증언 + 통화 3분: 20:04~20:08 아무도 못 봄"),
    (None, JJ, .8, 1.0, set(), 1, "옥상 R-1: 1층 뒤쪽 창 하나가 열려 있음(정준희가 열어 둔 화장실 창, 2026-11-17)"),
    (None, PH, 1.0, 1.0, set(), 2, "장면 3: 박혜수 핸드백의 채찍(노형철의 채찍 소리와 이어짐)"),
    (None, JH, .5, 1.0, set(), 2, "장면 3: 정형미 허리띠 가운데의 쓸린 자국"),
]

# 소거 추리: (필요 단서 집합들의 목록 중 하나라도, 빠지는 역할들, 빼는 무게, 적용 시작 단계)
ELIMINATIONS = [
    ([{"R-1", "H1"}, {"R-1", "E1"}], [PH], 2.0, 1),   # 창밖 투척 + 그 시각 2층 안에 있었던 흔적
]

# 전략적 조사: (역할, 단계) -> 먼저 고르는 단서(역할지에 이유가 있는 것)
STRATEGIC_FIRST = {(YJ, 0): ["C2"], (JJ, 0): ["C2"]}   # 아버지의 흔적
STRATEGIC_P = .8

# 풀이 경로: 이름 -> 필요 단서 집합(게시판 사실은 "BOARD:이름")
PATHS = {
    "투석구(J1+허리띠+R-1)": {"J1", "R-1"},
    "알리바이(D2+G2)": {"D2", "G2"},
    "정체(M1+R14·R16)": {"M1", "BOARD:R14·R16 유희철이 조직문화팀 초대 팀장"},
}

# =====================================================================
# 엔진
# =====================================================================
R = ROLES


def can(code, r, cracked):
    own = CLUES[code][1]
    if own is None:
        return True
    if own == "W":
        return code in cracked and r in cracked[code]
    return r != own.split(":")[1]


def run(policy="strategic", noise=0.0, lock_scale=1.0, hide_scale=1.0):
    holder, known, hidden = {}, set(), set()
    peek_hits = 0
    hand = defaultdict(list)
    jit = defaultdict(lambda: random.uniform(1 - noise, 1 + noise)) if noise else None
    said = [random.random() < t[3] for t in TESTIMONY]
    board = {b[0] for b in BOARD if random.random() < b[3]}
    snaps = []
    for si, (_, ap) in enumerate(STAGES):
        for c, v in CLUES.items():
            if v[0] == si and v[2]:
                known.add(c)
        # 잠긴 단서: 이 단계에서 언제 누가 푸는지
        crack_round, cracked = {}, {}
        if si == 0:
            for w, (p, who) in LOCKS.items():
                if random.random() < min(1, p * lock_scale):
                    crack_round[w] = (random.randint(3, ap), who)
        sinks = []
        for roles, s, p in AP_SINKS:
            if s == si:
                for r in roles:
                    if random.random() < p:
                        sinks.append((r, random.randint(1, max(ap, 1))))
        apl = {r: ap for r in R}
        peek_plan = {r: random.randint(1, max(ap, 1)) for roles, s_, p in PEEKS if s_ == si
                     for r in roles if random.random() < p}
        peekers = []
        for rd in range(1, ap + 1):
            for w, (cr, who) in crack_round.items():
                if cr == rd:
                    cracked[w] = who
            order = R[:]; random.shuffle(order)
            for r in order:
                if apl[r] <= 0:
                    continue
                if peek_plan.get(r) == rd:
                    peekers.append(r); apl[r] -= 1; continue
                sk = next((x for x in sinks if x[0] == r and x[1] <= rd), None)
                if sk:
                    sinks.remove(sk); apl[r] -= 1; continue
                avail = [c for c, v in CLUES.items() if v[0] == si and not v[2] and c not in holder and can(c, r, cracked)]
                if not avail:
                    continue
                c = next((x for x in avail if CLUES[x][1] == "W"), None)   # 번호를 알면 바로 연다
                if c is None and policy == "strategic":
                    pref = [x for x in STRATEGIC_FIRST.get((r, si), []) if x in avail]
                    if pref and random.random() < STRATEGIC_P:
                        c = pref[0]
                c = c or random.choice(avail)
                holder[c] = r; hand[r].append(c); apl[r] -= 1
        for c, r in holder.items():
            if CLUES[c][0] != si:
                continue
            hp = HIDE_SELF_P_CULPRIT if r == CULPRIT else HIDE_SELF_P
            if CLUES[c][3].get(r, 0) > 0 and random.random() < hp * hide_scale:
                hidden.add(c)
            else:
                known.add(c)
        for r in peekers:
            cand = [c for c in hidden if holder[c] != r]
            if cand:
                c = random.choice(cand)
                if random.random() < PEEK_SHARE_P:
                    hidden.discard(c); known.add(c); peek_hits += 1
        snaps.append(dict(p=pressure(known, board, si, said, jit, False),
                          pe=pressure(known, board, si, said, jit, True),
                          unfound=[c for c, v in CLUES.items() if v[0] == si and c not in holder and not v[2]]))
    kb = known | {"BOARD:" + b for b in board}
    paths = {n: req <= kb for n, req in PATHS.items()}
    return dict(snaps=snaps, paths=paths, held={r: len(hand[r]) for r in R}, known=known,
                hidden=set(hidden), holder=dict(holder), peek_hits=peek_hits)


def pressure(k, board, si, said, jit, elim):
    p = {r: 0.0 for r in R}
    J = (lambda key: jit[key]) if jit is not None else (lambda key: 1.0)
    mult = STAGE_MULT.get(si, {})
    kb = k | {"BOARD:" + b for b in board}
    for c in k:
        for r, v in CLUES[c][3].items():
            p[r] += v * mult.get(c, 1) * J(c)
    for i, (req, r, w, s0) in enumerate(COMBOS):
        if si >= s0 and req <= kb:
            p[r] += w * J(("combo", i))
    for i, t in enumerate(TESTIMONY):
        who, tgt, w, prob, req, s0, _ = t
        if si >= s0 and said[i] and req <= k:
            p[tgt] += w * J(("t", i))
    for name, tgt, w, prob, s0 in BOARD:
        if si >= s0 and name in board:
            p[tgt] += w * J(("b", name))
    if elim:
        for alts, roles, w, s0 in ELIMINATIONS:
            if si >= s0 and any(a <= k for a in alts):
                for r in roles:
                    p[r] -= w
    return p


def top_rates(ps):
    top = Counter()
    for p in ps:
        mx = max(p.values()); t = [r for r in R if p[r] == mx]
        for r in t:
            top[r] += 1 / len(t)
    return top


def report(name, n=20000, **kw):
    res = [run(**kw) for _ in range(n)]
    print(f"\n######## {name} (n={n}) ########")
    for si, (sname, _) in enumerate(STAGES):
        t = top_rates([x["snaps"][si]["p"] for x in res])
        te = top_rates([x["snaps"][si]["pe"] for x in res])
        avg = {r: st.mean(x["snaps"][si]["p"][r] for x in res) for r in R}
        print(f"[{sname} 끝] 1위: " + " ".join(f"{r} {t[r]/n*100:.0f}%" for r in R)
              + " | 소거 추리 해낸 경우: " + " ".join(f"{r} {te[r]/n*100:.0f}%" for r in R))
        print("   의심 합계 평균: " + " ".join(f"{r} {avg[r]:.1f}" for r in R))
        u = Counter(c for x in res for c in x["snaps"][si]["unfound"])
        print("   못 본 단서:", [(c, f"{v/n*100:.0f}%") for c, v in u.most_common(7)])
    last = [x["snaps"][-1]["pe"] for x in res]
    second = Counter(); close = 0
    for p in last:
        o = sorted(((v, r) for r, v in p.items() if r != CULPRIT), reverse=True)
        second[o[0][1]] += 1
        close += (p[CULPRIT] - o[0][0] < 1.0)
    print("마지막(소거 추리 포함) 범인 다음 후보: " + " ".join(f"{r} {second[r]/n*100:.0f}%" for r in R if r != CULPRIT)
          + f" | 범인과 차이 1점 미만 {close/n*100:.0f}%")
    pr = {k: sum(x["paths"][k] for x in res) / n for k in PATHS}
    anyp = sum(any(x["paths"].values()) for x in res) / n
    two = sum(sum(x["paths"].values()) >= 2 for x in res) / n
    print("풀이 경로: " + " / ".join(f"{k} {v*100:.0f}%" for k, v in pr.items()) + f" | 하나 이상 {anyp*100:.0f}% | 둘 이상 {two*100:.0f}%")
    print("보유 단서 평균: " + " ".join(f"{r} {st.mean(x['held'][r] for x in res):.1f}" for r in R))
    h = Counter(f"{c}({x['holder'][c]})" for x in res for c in x["hidden"])
    print("끝까지 숨겨진 단서(쥔 사람):", [(c, f"{v/n*100:.0f}%") for c, v in h.most_common(10)],
          f"| 엿보기로 드러난 단서 판당 {st.mean(x['peek_hits'] for x in res):.2f}개")
    unf0 = [len([c for c in x["snaps"][0]["unfound"] if CLUES[c][1] != "W"]) for x in res]
    print(f"조사 1단계 잠기지 않은 단서 미조사: 0개 {unf0.count(0)/n*100:.0f}%, 1개 이하 {sum(v<=1 for v in unf0)/n*100:.0f}%")
    return res


def contributions(si, n=5000, policy="strategic"):
    """단계 si 끝에서 역할별 의심을 만드는 단서·증언의 평균 기여"""
    tot = defaultdict(float)
    for _ in range(n):
        x = run(policy)
        k = {c for c in x["known"] if CLUES[c][0] <= si}
        mult = STAGE_MULT.get(si, {})
        for c in k:
            for r, v in CLUES[c][3].items():
                tot[(r, c)] += v * mult.get(c, 1) / n
    return tot


if __name__ == "__main__":
    random.seed(1)
    report("완전 랜덤", policy="random")
    report("전략적", policy="strategic")
    report("전략적, 무게 ±20%", policy="strategic", noise=.2)
    report("전략적, 무게 ±40%", policy="strategic", noise=.4)
    report("번호를 잘 푸는 팀(잠긴 단서 확률 x1.8)", policy="strategic", lock_scale=1.8)
    report("번호를 못 푸는 팀(x0.5)", policy="strategic", lock_scale=.5)
    report("참고: 아무도 숨기지 않음(1장 가정)", policy="strategic", hide_scale=0)
