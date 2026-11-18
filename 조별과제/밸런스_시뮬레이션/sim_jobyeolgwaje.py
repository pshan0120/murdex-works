"""조별과제 역할 밸런스 시뮬레이션 (2026-11-17)

방법: works/역할_밸런스_분석_방법.md
템플릿을 가져다 이 작품에 맞게 고친 것이다. 템플릿과 다른 점은 셋이다.
  1. 단서마다 AP 비용이 0~5로 다르다(인당 30 AP).
  2. 자료취합 단계에 학생증을 교환해야만 열리는 단서가 있다.
  3. 단서 연계(부모 단서를 조사해야 자식 단서가 열림)가 많다.

실행: python sim_jobyeolgwaje.py
"""
import random, sys, statistics as st
from collections import Counter, defaultdict
sys.stdout.reconfigure(encoding="utf-8")

LEE, HAN, CHOI, HWANG = "이준서", "한세린", "최도윤", "황기순"
ROLES = [LEE, HAN, CHOI, HWANG]
CULPRIT = LEE
ACCOMPLICE = None
HIDE_SELF_P = .8
HIDE_SELF_P_CULPRIT = .9
PEEK_AP = 3            # 뒷조사
PEEK_P = .5            # 단계마다 쓸 확률
PEEK_SHARE_P = .8
GOCHAL_AP = 3          # 이준서 고찰 3개(각 1 AP)

STAGES = [("자료조사", 30), ("자료취합", 30)]

# 학생증: 자료취합 시작 때 교환한다. 같은 학과(한세린·최도윤)끼리는 교환할 수 없다.
PAIRINGS = [((LEE, HAN), (CHOI, HWANG)), ((LEE, CHOI), (HAN, HWANG))]
GATHER_P = .6          # 컴공 학생증 두 장을 한 명이 모을 확률(추가 건네주기)

# 단서: 코드 -> dict(stage, ap, front, allow, parent, cards, w)
#   stage  : 조사할 수 있게 되는 단계 (0 자료조사 / 1 자료취합)
#   front  : 앞면으로 공개되어 AP 없이 모두가 보는 단서
#   allow  : 조사할 수 있는 역할(None이면 전원)
#   parent : 먼저 조사되어야 하는 단서
#   cards  : 소지해야 하는 학생증 주인
#   w      : 역할별 의심 무게
C = {}
def c(code, stage, ap, w=None, front=False, allow=None, parent=(), cards=()):
    C[code] = dict(stage=stage, ap=ap, front=front, allow=allow,
                   parent=set(parent), cards=set(cards), w=w or {})

# --- 앞면 공개(AP 0) ---
c("재난문자", 0, 0, front=True)
c("강의계획서", 0, 0, front=True)
c("건물보안", 0, 0, front=True)
c("시설안내도", 0, 0, front=True)
c("인상_이준서", 0, 0, front=True); c("인상_한세린", 0, 0, front=True)
c("인상_최도윤", 0, 0, front=True); c("인상_황기순", 0, 0, front=True)

# --- 학생증(개강에 각자 지급, 자료취합에서 교환하며 서로 보게 된다) ---
c("학생증_이준서", 1, 0, {LEE: .9}, front=True)
c("학생증_한세린", 1, 0, {HAN: .3}, front=True)
c("학생증_최도윤", 1, 0, {CHOI: .6}, front=True)
c("학생증_황기순", 1, 0, {HWANG: .9}, front=True)

# --- 강의실 ---
c("강의실1", 0, 2)                                   # 조원 이메일 목록
c("강의실2", 0, 2, {HAN: .2, CHOI: .2})              # 앞문 카드리더기
c("강의실3", 0, 2, {HWANG: .9})                      # 뒷문 틈새 긁힌 자국
c("강의실4", 0, 2, {LEE: .4})                        # 열린 창문, 비품창고 보임
c("강의실5", 0, 2, {HAN: .6})                        # 여성용 장갑 한 짝
c("강의실6", 0, 2)                                   # 발표용 PC
c("발표자료1", 0, 1, parent=["강의실6"])
c("발표자료2", 0, 1, {CHOI: .5}, parent=["강의실6"])
c("발표자료3", 0, 1, {HWANG: .8}, parent=["강의실6"])
c("발표자료4", 0, 1, {CHOI: .6}, parent=["강의실6"])

# --- 이과대학 ---
c("2층복도1", 0, 3, {LEE: .5, HWANG: .5})            # 젖은 발자국 두 줄(운동화·구두)
c("2층복도2", 0, 3)                                  # 정통과 연애 소문
c("게시판1", 0, 3, {CHOI: .3})                       # AI 칼럼
c("수학게시판1", 0, 3, {LEE: .3})                    # 옵튼AI 추천 채용
c("1층복도1", 1, 3)
c("행정실1", 1, 5, parent=["1층복도1"])
c("창고입구1", 1, 5, {LEE: .2}, parent=["행정실1"])
c("창고내부1", 1, 5, {LEE: .7}, parent=["창고입구1"])  # 사다리 발판의 굳지 않은 흙
c("2층복도3", 1, 4, {HAN: .3})                       # 단톡방 기록
c("게시판2", 1, 3, {HAN: .2})                        # 담배 포스트잇
c("게시판3", 1, 3)                                   # 비품창고 관리 안내
c("2층복도4", 1, 3, {LEE: .6})                       # 흙 묻은 발자국
c("2층복도5", 1, 3)                                  # 마른 발자국
c("학생회실1", 1, 5)
c("1층복도2", 1, 4)

# --- 원스탑(학생증 필요) ---
c("원스탑1", 1, 2, {LEE: -.2}, parent=["1층복도2"], cards=[LEE])
c("원스탑2", 1, 2, parent=["1층복도2"], cards=[HAN])
c("원스탑3", 1, 2, {CHOI: 1.2}, parent=["1층복도2"], cards=[CHOI])   # 18:05 접속
c("원스탑4", 1, 2, parent=["1층복도2"], cards=[HWANG])

# --- 수학과 구역 ---
c("수학휴게실1", 1, 5, {HWANG: 1.5}, allow=[LEE, HAN, CHOI], cards=[HWANG])
c("수학휴게실2", 1, 5, {HAN: .3, HWANG: .3}, allow=[LEE, HAN, CHOI], cards=[HWANG])
c("졸업생연락망1", 1, 2, parent=["학생회실1"])
c("통화1", 1, 2, {HWANG: .3}, allow=[LEE, HAN, CHOI], parent=["졸업생연락망1"])
c("통화2", 1, 2, {HWANG: .8}, allow=[HAN, CHOI], parent=["통화1"])

# --- 컴공과 구역 ---
c("동아리실1", 0, 5, {HAN: .4})
c("컴공게시판1", 0, 3)                               # 개인과제 → 조별과제 변경
c("컴공휴게실1", 1, 5, {HAN: .4}, allow=[LEE, HWANG], cards=[HAN, CHOI])
c("컴공휴게실2", 1, 5, {HAN: .5, LEE: .3}, allow=[LEE, HWANG], cards=[HAN, CHOI])
c("컴공휴게실3", 1, 5, {CHOI: .8, HAN: .5}, cards=[HAN, CHOI])       # USB

# --- 정보통계학과 구역 ---
c("정통사무실1", 0, 5, {LEE: .4})                    # 옵튼AI 우수학생 추천
c("정통휴게실1", 1, 5, {LEE: .9}, allow=[HAN, CHOI, HWANG], cards=[LEE])

# --- 인물 단서(본인은 조사할 수 없다) ---
c("이준서1", 0, 3, {LEE: .8}, allow=[HAN, CHOI, HWANG])   # 운동화에 눈, 크고 넉넉함
c("이준서2", 0, 5, {LEE: .8}, allow=[HAN, CHOI, HWANG])   # 공군 정비, 높은 곳 작업
c("이준서3", 0, 5, {LEE: .5}, allow=[HAN, CHOI, HWANG])   # 자리 옮김, 조장 자청
c("이준서4", 0, 5, {LEE: .1}, allow=[HAN, CHOI, HWANG])
c("이준서5", 1, 3, {LEE: .8}, allow=[HAN, CHOI, HWANG])   # 운동화에 물기
c("한세린1", 0, 3, {HAN: .3}, allow=[LEE, CHOI, HWANG])
c("한세린2", 0, 5, {HAN: .2}, allow=[LEE, CHOI, HWANG])
c("한세린3", 0, 5, {HAN: .3, CHOI: .3}, allow=[LEE, CHOI, HWANG])
c("한세린4", 0, 5, {HAN: .3}, allow=[LEE, CHOI, HWANG])
c("한세린5", 1, 5, {HAN: .4}, allow=[LEE, CHOI, HWANG])
c("한세린6", 1, 2, {CHOI: .9}, allow=[LEE, CHOI], parent=["한세린5"])
c("한세린7", 1, 2, {HAN: 1.0}, allow=[LEE], parent=["한세린6"])
c("한세린8", 1, 2, {HAN: .5, LEE: .2}, allow=[HWANG], parent=["한세린5"])
c("최도윤1", 0, 3, {CHOI: .4}, allow=[LEE, HAN, HWANG])
c("최도윤2", 0, 5, {CHOI: .7}, allow=[LEE, HAN, HWANG])   # 옵튼AI 채점 도입
c("최도윤3", 0, 4, {CHOI: .4}, allow=[LEE, HAN, HWANG])
c("최도윤4", 1, 3, {CHOI: -.5}, allow=[LEE, HAN, HWANG])  # 신발이 깨끗하다
c("최도윤5", 1, 5, {CHOI: 1.2}, allow=[LEE, HAN, HWANG])  # 커서가 혼자 움직임
c("황기순1", 0, 5, {HWANG: .6}, allow=[LEE, HAN, CHOI])
c("황기순2", 0, 5, {HWANG: .5}, allow=[LEE, HAN, CHOI])
c("황기순3", 0, 5, {HWANG: .5}, allow=[LEE, HAN, CHOI])   # 아이콘 정리 습관
c("황기순4", 0, 5, {HWANG: .4}, allow=[LEE, HAN, CHOI])   # 문서 편집, 행정병
c("황기순5", 0, 3, {HWANG: .6}, allow=[LEE, HAN, CHOI])   # 구두에 눈
c("황기순6", 1, 3, {HWANG: .5}, allow=[LEE, HAN, CHOI])   # 구두 물기, 굽이 높음

# 단서 짝: 두 장이 모여야 뜻이 서는 것
COMBOS = [
    ({"이준서1", "2층복도1"}, LEE, .6, 0),
    ({"이준서1", "2층복도4"}, LEE, .8, 1),
    ({"창고내부1", "강의실4"}, LEE, 1.0, 1),
    ({"창고내부1", "이준서2"}, LEE, .8, 1),
    ({"정통휴게실1", "학생증_이준서"}, LEE, 1.0, 1),
    ({"강의실3", "학생증_황기순"}, HWANG, 1.0, 1),
    ({"2층복도1", "황기순6"}, HWANG, .5, 1),
    ({"발표자료3", "황기순4"}, HWANG, .6, 0),
    ({"통화2", "강의실1"}, HWANG, 1.0, 1),
    ({"최도윤5", "발표자료2"}, CHOI, .6, 0),
    ({"최도윤2", "컴공게시판1"}, CHOI, .6, 0),
    ({"원스탑3", "최도윤4"}, CHOI, .4, 1),
    ({"컴공휴게실3", "최도윤5"}, CHOI, .5, 1),
    ({"한세린1", "한세린2"}, HAN, .3, 0),
]

# 역할지 속 증언: (말하는 역할, 대상, 무게, 꺼낼 확률, 필요 단서, 설명)
TESTIMONY = [
    (HAN, HAN, .4, .8, set(), "한세린: 17:45 다이어리 가지러 강의실에 다시 들어갔다"),
    (HAN, HWANG, .3, .8, set(), "한세린: 그때 누군가 황급히 화장실로 들어가는 소리를 들었다"),
    (HAN, HAN, .5, 1.0, set(), "한세린: 19:00 발표자 노트가 지워진 것을 처음 발견했다"),
    (HAN, HAN, .2, .7, {"강의실5"}, "한세린: 장갑을 두고 와서 혼자 강의실로 되돌아갔다"),
    (CHOI, LEE, .8, .85, set(), "최도윤: 18:35 이준서가 급히 화장실로 들어가는 것을 보았다"),
    (CHOI, CHOI, .5, .10, set(), "최도윤: 18:00~18:30 원스탑 공용 PC를 썼다"),
    (CHOI, CHOI, .4, .20, set(), "최도윤: 18:45~19:20 컴공과 휴게실에 혼자 있었다"),
    (HWANG, HWANG, .9, .15, set(), "황기순: 학생증으로 뒷문을 긁어 열고 들어갔다"),
    (HWANG, HWANG, .6, .15, set(), "황기순: 발표용 PC를 켜고 아이콘을 옮겼다"),
    (HWANG, HWANG, .6, .85, set(), "황기순: 18:40~18:50 강의실에서 한세린을 만났다"),
    (HWANG, HAN, .3, .85, set(), "황기순: 그때 한세린도 강의실에 있었다"),
]

# 소거 추리: (필요 단서, 빠지는 역할, 빼는 무게)
ELIMINATIONS = [
    ({"최도윤4", "2층복도4"}, [CHOI], .8),          # 신발이 깨끗하니 흙 발자국의 주인이 아니다
    ({"강의실2", "강의실3", "학생증_황기순"}, [HAN, CHOI], .5),  # 학생증으로 들어갈 수 있는 사람은 문을 긁을 이유가 없다
]

# 전략적 조사: 역할지 지침에 먼저 열 이유가 적힌 단서
STRATEGIC_FIRST = {
    (CHOI, 1): ["컴공휴게실3"],                       # 자료조사 단계 지침: 잃어버린 USB를 찾아라
    (LEE, 1): ["1층복도1", "행정실1", "창고입구1", "창고내부1"],   # 범인이 사다리 흔적을 먼저 쥐려는 경우
    (HWANG, 1): ["1층복도2", "원스탑3"],
}
STRATEGIC_P = .8

# 풀이 경로: 범인(이준서)에 이르는 묶음
PATHS = {
    "사다리와 창문": ({"창고내부1", "강의실4"}, False),
    "신발 자국": ({"이준서1", "2층복도4"}, False),
    "목격 증언": (set(), False),          # 최도윤의 증언으로만 서는 경로(아래에서 따로 처리)
    "동기(전지혜)": ({"정통휴게실1", "학생증_이준서"}, False),
}

# =====================================================================
# 엔진
# =====================================================================
R = ROLES
FRONT_BY_STAGE = defaultdict(list)
for code, v in C.items():
    if v["front"]:
        FRONT_BY_STAGE[v["stage"]].append(code)


def deal_cards():
    """자료취합 시작의 학생증 교환. 역할 -> 소지한 학생증 주인 집합."""
    hold = {r: set() for r in R}
    for a, b in random.choice(PAIRINGS):
        hold[a].add(b); hold[b].add(a)
    if random.random() < GATHER_P:          # 컴공 두 장을 한 명이 모으는 추가 건네주기
        g = random.choice([LEE, HWANG])
        hold[g] |= {HAN, CHOI}
    return hold


def run(policy="strategic", noise=0.0, action_scale=1.0, hide_scale=1.0, lee_bury=True):
    found, known, hidden = set(), set(), set()
    holder = {}
    hold_cards = {r: {r} for r in R}
    jit = defaultdict(lambda: random.uniform(1 - noise, 1 + noise)) if noise else None
    said = {i: random.random() < t[3] for i, t in enumerate(TESTIMONY)}
    snaps, peek_hits = [], 0

    for si in range(len(STAGES)):
        if si == 1:
            hold_cards = deal_cards()
        for code in FRONT_BY_STAGE[si]:
            found.add(code); known.add(code)
        ap = {r: STAGES[si][1] for r in R}
        if action_scale:                                  # 이준서 고찰 3개
            ap[LEE] -= GOCHAL_AP
        peekers = [r for r in R if random.random() < PEEK_P and ap[r] >= PEEK_AP]
        for r in peekers:
            ap[r] -= PEEK_AP

        while True:
            moved = False
            order = R[:]; random.shuffle(order)
            for r in order:
                av = [x for x in C
                      if x not in found and not C[x]["front"] and C[x]["stage"] <= si
                      and C[x]["ap"] <= ap[r]
                      and (C[x]["allow"] is None or r in C[x]["allow"])
                      and C[x]["parent"] <= found
                      and C[x]["cards"] <= hold_cards[r]]
                if not av:
                    continue
                pick = None
                if policy == "strategic":
                    pref = [x for x in STRATEGIC_FIRST.get((r, si + 1), []) if x in av]
                    if pref and random.random() < STRATEGIC_P:
                        pick = pref[0]
                pick = pick or random.choice(av)
                found.add(pick); holder[pick] = r; ap[r] -= C[pick]["ap"]; moved = True
            if not moved:
                break

        for code in found:
            if code in known or code in hidden:
                continue
            r = holder.get(code)
            if r is None:
                known.add(code); continue
            w = C[code]["w"].get(r, 0)
            hp = HIDE_SELF_P_CULPRIT if r == CULPRIT else HIDE_SELF_P
            bury = w > 0 and random.random() < hp * hide_scale
            if r == CULPRIT and not lee_bury:
                bury = False
            if bury:
                hidden.add(code)
            else:
                known.add(code)
        for r in peekers:
            cand = [x for x in hidden if holder.get(x) != r]
            if cand:
                x = random.choice(cand)
                if random.random() < PEEK_SHARE_P:
                    hidden.discard(x); known.add(x); peek_hits += 1
        snaps.append(dict(p=pressure(known, si, said, jit, False),
                          pe=pressure(known, si, said, jit, True),
                          unfound=[x for x in C if C[x]["stage"] <= si and x not in found]))

    paths = {n: req <= known for n, (req, _) in PATHS.items() if req}
    paths["목격 증언"] = said[4]
    return dict(snaps=snaps, paths=paths, hidden=set(hidden), peek_hits=peek_hits,
                known=set(known))


def pressure(k, si, said, jit, elim):
    p = {r: 0.0 for r in R}
    J = (lambda key: jit[key]) if jit is not None else (lambda key: 1.0)
    for code in k:
        for r, v in C[code]["w"].items():
            p[r] += v * J(code)
    for i, (req, r, w, s0) in enumerate(COMBOS):
        if si >= s0 and req <= k:
            p[r] += w * J(("combo", i))
    for i, (_, tgt, w, _, req, _) in enumerate(TESTIMONY):
        if said[i] and req <= k:
            p[tgt] += w * J(("t", i))
    if elim:
        for req, roles, w in ELIMINATIONS:
            if req <= k:
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
              + " | 소거 추리: " + " ".join(f"{r} {te[r]/n*100:.0f}%" for r in R))
        print("   평균 의심: " + " ".join(f"{r} {avg[r]:.1f}" for r in R))
        u = Counter(x for v in res for x in v["snaps"][si]["unfound"])
        print("   못 본 단서:", [(x, f"{v/n*100:.0f}%") for x, v in u.most_common(5)])
    last = [x["snaps"][-1]["p"] for x in res]
    second, close = Counter(), 0
    for p in last:
        o = sorted(((v, r) for r, v in p.items() if r != CULPRIT), reverse=True)
        second[o[0][1]] += 1
        close += (p[CULPRIT] - o[0][0] < 1.0)
    print("범인 다음: " + " ".join(f"{r} {second[r]/n*100:.0f}%" for r in R if r != CULPRIT)
          + f" | 범인과 차이 1점 미만 {close/n*100:.0f}%")
    pr = {k: sum(x["paths"].get(k, False) for x in res) / n for k in PATHS}
    print("풀이 경로: " + " / ".join(f"{k} {v*100:.0f}%" for k, v in pr.items())
          + f" | 하나 이상 {sum(any(x['paths'].values()) for x in res)/n*100:.0f}%"
          + f" | 둘 이상 {sum(sum(x['paths'].values())>=2 for x in res)/n*100:.0f}%")
    h = Counter(x for v in res for x in v["hidden"])
    print("끝까지 숨겨진 단서:", [(x, f"{v/n*100:.0f}%") for x, v in h.most_common(6)],
          f"| 엿보기로 드러남 판당 {st.mean(x['peek_hits'] for x in res):.2f}개")


def contribution(role, n=4000):
    """마지막 단계에서 그 역할의 의심을 키우는 재료별 평균 기여."""
    acc = Counter()
    for _ in range(n):
        k = run()["known"]
        for code in k:
            if C[code]["w"].get(role, 0):
                acc[code] += C[code]["w"][role]
        for req, r, w, s0 in COMBOS:
            if r == role and req <= k:
                acc["[짝] " + "+".join(sorted(req))] += w
        for i, (_, tgt, w, prob, req, desc) in enumerate(TESTIMONY):
            if tgt == role and req <= k:
                acc["[증언] " + desc[:26]] += w * prob
    print(f"\n######## {role} 의심의 출처 (판당 평균 기여) ########")
    for code, v in acc.most_common(12):
        print(f"  {code:30s} {v/n:.2f}")


def witness_effect(n=20000):
    """최도윤의 목격 증언이 나온 판과 안 나온 판을 나눠 본다."""
    res = [run() for _ in range(n)]
    for flag in (True, False):
        g = [x for x in res if x["paths"]["목격 증언"] is flag]
        if not g:
            continue
        t = top_rates([x["snaps"][-1]["p"] for x in g])
        avg = st.mean(x["snaps"][-1]["p"][LEE] for x in g)
        gap = st.mean(x["snaps"][-1]["p"][LEE] - max(v for r, v in x["snaps"][-1]["p"].items() if r != LEE) for x in g)
        print(f"목격 증언 {'나옴' if flag else '안 나옴'} ({len(g)/n*100:.0f}%): "
              f"마지막 1위 " + " ".join(f"{r} {t[r]/len(g)*100:.0f}%" for r in R)
              + f" | 이준서 평균 {avg:.1f} | 2위와 차이 {gap:+.1f}")


if __name__ == "__main__":
    random.seed(1)
    report("완전 랜덤", policy="random")
    report("전략적", policy="strategic")
    report("전략적, 무게 ±40%", policy="strategic", noise=.4)
    report("이준서가 사다리 흔적을 숨기지 않음", policy="strategic", lee_bury=False)
    report("참고: 아무도 숨기지 않음", policy="strategic", hide_scale=0)
    contribution(LEE)
    contribution(HWANG)
    print("\n######## 최도윤의 목격 증언 효과 ########")
    witness_effect()
