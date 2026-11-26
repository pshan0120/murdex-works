"""2026-11-26 노형철·정준희 용의점 보강 안 예상치.
노형철 안: 하도훈 수첩 A9에 "그 글, 여 팀장님 수첩 글씨랑 같다. 22일 조사 때 말해 볼까" → 하도훈이 고백글의 출처를 조사 자리에서 꺼내려 했다(입막음 동기).
정준희 안 1: 하도훈 수첩 A8에 "2008 영업본부 인사 자료. 정태호 상무 퇴직. 정 씨?" → 하도훈이 정준희의 정체에 다가갔다(입막음 동기).
정준희 안 2: 첫 발견자. 사무실에 들러 가방을 챙긴 뒤 탕비실에 가서, 올라가고 1~2분 뒤에 비명이 났다(다른 역할 타임라인).
실행: python sim_narul_nh_jj_1126.py
"""
import random, copy
import sim_narul as S

BASE = dict(C=copy.deepcopy(S.CLUES), CO=list(S.COMBOS), T=list(S.TESTIMONY))


def reset():
    S.CLUES.clear(); S.CLUES.update(copy.deepcopy(BASE["C"])); S.COMBOS[:] = BASE["CO"]; S.TESTIMONY[:] = BASE["T"]


def nh():
    S.CLUES["A9"] = (0, "NOT:" + S.NH, False, {S.NH: 1.6})
    S.COMBOS.append(({"A9", "W4"}, S.NH, .5, 0))


def jj1():
    S.CLUES["A8"] = (0, "NOT:" + S.JJ, False, {S.JJ: 2.0})
    S.COMBOS.append(({"A8", "W5"}, S.JJ, .5, 0))
    S.COMBOS.append(({"A8", "C2"}, S.JJ, .3, 0))


def jj2():
    S.TESTIMONY.append((None, S.JJ, .6, 1.0, set(), 0, "공지: 정준희가 올라가고 1~2분 뒤 비명"))


def show(name, n=10000):
    random.seed(13)
    res = [S.run(policy="strategic") for _ in range(n)]
    for si in (1, 2):
        t = S.top_rates([x["snaps"][si]["p"] for x in res])
        print(f"{name:16s} {S.STAGES[si][0]} 1위 " + " ".join(f"{r} {t[r]/n*100:.0f}%" for r in S.R))
    last = [x["snaps"][-1]["pe"] for x in res]
    te = S.top_rates(last)
    close = sum(1 for p in last if p[S.JH] - max(v for r, v in p.items() if r != S.JH) < 1.0) / n
    print(f"{'':16s} 소거 포함 3단계 1위 " + " ".join(f"{r} {te[r]/n*100:.0f}%" for r in S.R) + f" | 접전 {close*100:.0f}%")


def jj3():
    """D3 "체구가 아주 작은 사람이 아니면 드나들 수 없는 크기" + 정준희 외형(160cm대 초반, 마른 체격): 화장실 창으로 나갔다 들어왔을 수 있다."""
    S.COMBOS.append(({"D3"}, S.JJ, .8, 1))
    S.COMBOS.append(({"D3"}, S.JH, .3, 1))   # 정형미(150cm대 중반)도 해당하지만 화장실에 있지 않았다


reset(); show("지금")
reset(); jj1(); jj2(); jj3(); show("정준희 안 1+2+3")
reset(); nh(); jj1(); jj2(); jj3(); show("모두+3")
reset(); nh(); show("노형철 안")
reset(); jj1(); jj2(); show("정준희 안 1+2")
reset(); nh(); jj1(); jj2(); show("모두")
