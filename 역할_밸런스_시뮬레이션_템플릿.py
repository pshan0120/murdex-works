"""역할 밸런스 시뮬레이션 템플릿 (2026-11-17, 같은 날 자기 불리 단서 숨김·엿보기 추가)

방법은 works/역할_밸런스_분석_방법.md 를 본다.
쓰는 법: 이 파일을 작품 폴더의 밸런스_시뮬레이션/ 으로 복사한 뒤 "작품별 설정" 부분만 채운다.
아래 설정은 돌아가는지 확인하려고 넣은 4인 견본이다. 실제 작품 내용이 아니다.
참고 구현: works/튜토리얼/밸런스_시뮬레이션/sim_tutorial.py

실행: python 역할_밸런스_시뮬레이션_템플릿.py
"""
import random, sys, statistics as st
from collections import Counter, defaultdict
sys.stdout.reconfigure(encoding="utf-8")

# =====================================================================
# 작품별 설정 (여기만 채운다)
# =====================================================================
ROLES = ["가", "나", "다", "라"]
CULPRIT = "가"
ACCOMPLICE = None          # 범인 조력자 역할이 있을 때만 이름을 넣는다. 드물다.
ACCOMPLICE_HIDE_P = .6     # 조력자가 범인에게 불리한 단서를 쥐었을 때 숨길 확률
HIDE_SELF_P = .8           # 찾은 사람 자신에게 불리한 단서를 숨길 확률(2026-11-17 사용자 지정)
HIDE_SELF_P_CULPRIT = .9   # 범인일 때
# 엿보기: (역할들, 단계, 쓸 확률). AP 1을 쓰고 남이 숨긴 단서 하나를 본 뒤 PEEK_SHARE_P 확률로 공개한다. 없으면 [].
PEEKS = [(["가", "나", "다", "라"], 0, .5)]
PEEK_SHARE_P = .8

# 조사 단계: (이름, 인당 AP)
STAGES = [("1차 조사", 5), ("2차 조사", 2)]

# 단서: 코드 -> (단계 번호 0부터, 조사 제한, 조사 즉시 전원 공개 여부, {역할: 의심 무게})
#   조사 제한: None = 누구나 / "ONLY:역할" = 그 역할만 / "NOT:역할" = 그 역할 빼고(인물 단서)
#   즉시 공개 단서는 숨길 수 없다. 나머지는 찾은 사람에게 불리하면(무게 > 0) HIDE_SELF_P로 숨긴다.
#   "NOT:역할" 인물 단서는 본인이 못 집으므로 자연히 공개된다.
#   무게: 의심을 키우면 +, 혐의를 벗겨 주면 -. 대략 0.3 약함 / 1.0 보통 / 1.5~2.0 강한 동기·물증
CLUES = {
    "P1": (0, None, True, {"가": .3, "나": .3}),
    "P2": (0, None, True, {"다": 1.5}),
    "P3": (0, "ONLY:나", True, {"나": -.5}),
    "P4": (0, None, True, {}),
    "가1": (0, "NOT:가", False, {"가": .5}), "나1": (0, "NOT:나", False, {"나": 1.5}),
    "다1": (0, "NOT:다", False, {"다": 1.0}), "라1": (0, "NOT:라", False, {"라": 1.8}),
    "Q1": (1, None, True, {"가": 1.0}),
    "가2": (1, "NOT:가", False, {"가": .8}), "라2": (1, "NOT:라", False, {"라": -.6}),
}

# 단서 짝: 두 장 이상이 함께 나와야 뜻이 서는 것. (필요 단서 집합, 역할, 무게, 이 단계부터 셈)
COMBOS = [
    ({"P1", "가1"}, "가", .8, 0),
    ({"P2", "다1"}, "다", .5, 0),
    ({"Q1", "P1"}, "가", .6, 1),
]

# 역할지 속 증언: (말하는 역할 또는 None=공지 사실, 대상, 무게, 꺼낼 확률, 필요 단서 집합, 설명)
#   말할 사람이 숨길 이유가 없으면 확률은 1.0. 자기 비밀과 얽힌 말만 1.0 미만으로 둔다.
TESTIMONY = [
    ("나", "라", .5, 1.0, set(), "나: 라가 그날 다퉜다"),
    (None, "나", .3, 1.0, set(), "공지 사실: 나가 시신 첫 발견"),
]

# 소거 추리: 플레이어가 따져서 혐의를 빼는 경우. (필요 단서·증언 집합, 빠지는 역할들, 빼는 무게)
#   압박 결과와 따로 "추리를 해낸 경우"로 보고한다.
ELIMINATIONS = [
    ({"P1", "P3"}, ["나", "다", "라"], .8),
]

# 역할 액션: 범인 액션 등. 대상 단서가 아직 조사되지 않았을 때만 쓸 수 있다고 본다.
ACTIONS = [
    dict(role="가", stage=1, target="Q1", p=.8, ap=1, variant={"가": .3}),
]

# 전략적 조사: (역할, 단계) -> 먼저 고르는 단서 목록(역할지에 "당신만 열 수 있다"가 있는 것 등)
STRATEGIC_FIRST = {("나", 0): ["P3"]}
STRATEGIC_P = .8

# 풀이 경로: 이름 -> (필요 단서 집합, 액션이 쓰이면 막히는 경로인지)
PATHS = {
    "물증": ({"P1", "가1"}, False),
    "블랙박스류": ({"Q1"}, True),
}

# =====================================================================
# 엔진 (여기부터는 손대지 않아도 된다)
# =====================================================================
R = ROLES


def can(code, r):
    own = CLUES[code][1]
    if own is None:
        return True
    kind, who = own.split(":")
    return (r == who) if kind == "ONLY" else (r != who)


def run(policy="strategic", noise=0.0, action_scale=1.0, hide_scale=1.0):
    holder, known, used, hidden = {}, set(), set(), set()
    hand = defaultdict(list)
    jit = defaultdict(lambda: random.uniform(1 - noise, 1 + noise)) if noise else None
    said = {i: random.random() < t[3] for i, t in enumerate(TESTIMONY)}
    snaps = []
    peek_hits = 0
    for si, (_, ap) in enumerate(STAGES):
        apl = {r: ap for r in R}
        peek_plan = {r: random.randint(1, max(ap, 1)) for roles, s, p in PEEKS if s == si
                     for r in roles if random.random() < p}
        peekers = []
        for rd in range(1, ap + 1):
            order = R[:]; random.shuffle(order)
            for r in order:
                if apl[r] <= 0:
                    continue
                if peek_plan.get(r) == rd:
                    peekers.append(r); apl[r] -= 1; continue
                act = next((a for a in ACTIONS if a["role"] == r and a["stage"] == si and id(a) not in used
                            and a["target"] not in holder and random.random() < a["p"] * action_scale), None)
                if act:
                    used.add(id(act)); apl[r] -= act["ap"]; continue
                avail = [c for c, v in CLUES.items() if v[0] == si and c not in holder and can(c, r)]
                if not avail:
                    continue
                c = None
                if policy == "strategic":
                    pref = [x for x in STRATEGIC_FIRST.get((r, si), []) if x in avail]
                    if pref and random.random() < STRATEGIC_P:
                        c = pref[0]
                c = c or random.choice(avail)
                holder[c] = r; hand[r].append(c); apl[r] -= 1
        for c, r in holder.items():
            if CLUES[c][0] != si:
                continue
            if not CLUES[c][2]:
                if r == ACCOMPLICE and CLUES[c][3].get(CULPRIT, 0) > 0 and random.random() < ACCOMPLICE_HIDE_P:
                    hidden.add(c); continue
                hp = HIDE_SELF_P_CULPRIT if r == CULPRIT else HIDE_SELF_P
                if CLUES[c][3].get(r, 0) > 0 and random.random() < hp * hide_scale:
                    hidden.add(c); continue
            known.add(c)
        for r in peekers:   # 엿보기: 남이 숨긴 단서 하나
            cand = [c for c in hidden if holder[c] != r]
            if cand:
                c = random.choice(cand)
                if random.random() < PEEK_SHARE_P:
                    hidden.discard(c); known.add(c); peek_hits += 1
        variants = {a["target"]: a["variant"] for a in ACTIONS if id(a) in used}
        snaps.append(dict(p=pressure(known, si, variants, said, jit, False),
                          pe=pressure(known, si, variants, said, jit, True),
                          unfound=[c for c, v in CLUES.items() if v[0] == si and c not in holder]))
    acted = bool(used)
    hit = {a["target"] for a in ACTIONS if id(a) in used}
    paths = {n: req <= known and not (blocked and hit & req) for n, (req, blocked) in PATHS.items()}
    return dict(snaps=snaps, acted=acted, paths=paths, held={r: len(hand[r]) for r in R},
                hidden=set(hidden), peek_hits=peek_hits)


def pressure(k, si, variants, said, jit, elim):
    p = {r: 0.0 for r in R}
    J = (lambda key: jit[key]) if jit is not None else (lambda key: 1.0)
    for c in k:
        for r, v in variants.get(c, CLUES[c][3]).items():
            p[r] += v * J(c)
    for i, (req, r, w, s0) in enumerate(COMBOS):
        if si >= s0 and req <= k:
            p[r] += w * J(("combo", i))
    for i, (who, tgt, w, prob, req, _) in enumerate(TESTIMONY):
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
        print(f"[{sname} 끝] 1위: " + " ".join(f"{r} {t[r]/n*100:.0f}%" for r in R)
              + " | 소거 추리 해낸 경우: " + " ".join(f"{r} {te[r]/n*100:.0f}%" for r in R))
        u = Counter(c for x in res for c in x["snaps"][si]["unfound"])
        print("   못 본 단서:", [(c, f"{v/n*100:.0f}%") for c, v in u.most_common(5)])
    last = [x["snaps"][-1]["p"] for x in res]
    second = Counter(); close = 0
    for p in last:
        o = sorted(((v, r) for r, v in p.items() if r != CULPRIT), reverse=True)
        second[o[0][1]] += 1
        close += (p[CULPRIT] - o[0][0] < 1.0)
    print("범인 다음으로 의심받는 사람: " + " ".join(f"{r} {second[r]/n*100:.0f}%" for r in R if r != CULPRIT)
          + f" | 범인과 차이 1점 미만 {close/n*100:.0f}%")
    if ACTIONS:
        a = [x for x in res if x["acted"]]; b = [x for x in res if not x["acted"]]
        ta = top_rates([x["snaps"][-1]["p"] for x in a]) if a else Counter()
        tb = top_rates([x["snaps"][-1]["p"] for x in b]) if b else Counter()
        print(f"액션 사용 {len(a)/n*100:.0f}% | 마지막 단계 범인 1위: 쓴 판 {ta[CULPRIT]/max(len(a),1)*100:.0f}%, 안 쓴 판 {tb[CULPRIT]/max(len(b),1)*100:.0f}%")
    pr = {k: sum(x["paths"][k] for x in res) / n for k in PATHS}
    anyp = sum(any(x["paths"].values()) for x in res) / n
    two = sum(sum(x["paths"].values()) >= 2 for x in res) / n
    print("풀이 경로: " + " / ".join(f"{k} {v*100:.0f}%" for k, v in pr.items()) + f" | 하나 이상 {anyp*100:.0f}% | 둘 이상 {two*100:.0f}%")
    print("보유 단서 평균: " + " ".join(f"{r} {st.mean(x['held'][r] for x in res):.1f}" for r in R))
    h = Counter(c for x in res for c in x["hidden"])
    print("끝까지 숨겨진 단서:", [(c, f"{v/n*100:.0f}%") for c, v in h.most_common(6)],
          f"| 엿보기로 드러난 단서 판당 {st.mean(x['peek_hits'] for x in res):.2f}개")


if __name__ == "__main__":
    random.seed(1)
    report("완전 랜덤", policy="random")
    report("전략적", policy="strategic")
    report("전략적, 무게 ±40%", policy="strategic", noise=.4)
    if ACTIONS:
        report("액션을 안 씀", policy="strategic", action_scale=0)
    report("참고: 아무도 숨기지 않음", policy="strategic", hide_scale=0)
