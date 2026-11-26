"""2026-11-26 유정석·정준희 의심거리 보강 안 예상치.
정준희 안: 옥상 R-1에 "열린 1층 창은 탕비실 창 가까이" → 맨손으로도 닿는 거리라는 의심(D3와 맞추면 정준희).
유정석 안: 사내 야구 동호회 투수(게시판) + 20:04~20:08 아무도 못 봄(P7) + 탕비실 창 아래 자기 차(G3) → 맨손 투척 의심.
실행: python sim_narul_suspect_options_1126.py
"""
import random, copy
import sim_narul as S

BASE = dict(T=list(S.TESTIMONY), B=list(S.BOARD), C=list(S.COMBOS))


def reset():
    S.TESTIMONY[:] = BASE["T"]; S.BOARD[:] = BASE["B"]; S.COMBOS[:] = BASE["C"]


def jj():
    S.TESTIMONY.append((None, S.JJ, 1.0, 1.0, {"D3"}, 1, "R-1: 열린 1층 창이 탕비실 창 가까이(맨손 거리) + D3 → 정준희"))


def yj():
    S.BOARD.append(("야구 동호회 투수 유정석", S.YJ, .6, .6, 1))
    S.COMBOS.append(({"P7", "G3"}, S.YJ, .5, 1))


def show(name):
    random.seed(5)
    n = 10000
    res = [S.run(policy="strategic") for _ in range(n)]
    for si in (1, 2):
        t = S.top_rates([x["snaps"][si]["p"] for x in res])
        print(f"{name:22s} {S.STAGES[si][0]} 1위 " + " ".join(f"{r} {t[r]/n*100:.0f}%" for r in S.R))
    last = [x["snaps"][-1]["pe"] for x in res]
    close = sum(1 for p in last if p[S.JH] - max(v for r, v in p.items() if r != S.JH) < 1.0) / n
    te = S.top_rates(last)
    print(f"{'':22s} 소거 포함 3단계 1위 " + " ".join(f"{r} {te[r]/n*100:.0f}%" for r in S.R) + f" | 접전 {close*100:.0f}%")


BASE_A13 = S.CLUES["A13"]
BASE_MULT = dict(S.STAGE_MULT[1])


def yj_pebble():
    """사용자 안(2026-11-26): 화분 흙 위 조약돌(멀칭). 조약돌로 내리친 뒤 창밖 화단으로 떨어뜨렸다는 착각.
    창밖 투척이 드러난 뒤에도 힘이 빠지지 않고(떨어뜨린 돌이 앞유리에 맞았다는 해석까지 가능), R-1과 짝이 된다."""
    S.CLUES["A13"] = (0, "NOT:" + S.YJ, False, {S.YJ: 1.0})
    S.STAGE_MULT[1]["A13"] = 1.0
    S.COMBOS.append(({"A13", "R-1"}, S.YJ, .5, 1))


def reset2():
    reset(); S.CLUES["A13"] = BASE_A13; S.STAGE_MULT[1].clear(); S.STAGE_MULT[1].update(BASE_MULT)


reset2(); show("지금 정본")
reset2(); jj(); show("정준희 안")
reset2(); yj_pebble(); show("유정석 조약돌 안")
reset2(); jj(); yj_pebble(); show("정준희 + 조약돌")
