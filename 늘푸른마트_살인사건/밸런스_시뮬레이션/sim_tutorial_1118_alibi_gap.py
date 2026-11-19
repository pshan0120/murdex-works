"""2026-11-18 서지훈·최유나가 서로 알리바이를 메워 주는 문제: 빈틈안 비교 (미적용, sim_tutorial.py 정본 위에 덧씌움)

제안(31장):
- 서지훈: 담배 손님(POS 02:19) 뒤 매장 안쪽 진열대에서 우산·우비를 채움 → 카운터와 창가가 안 보임.
  02:10 "02:30까지 창고 문으로 드나든 사람 못 봄" → "카운터에 있는 동안에는 못 봄".
- 최유나: 01:30 "알바생은 거의 카운터에 있었다" 삭제. 담배 손님 뒤 번역 원고에 빠져 몇 분 화면만 봄(정문 종소리는 없었음).
  02:24 커피: "카운터에 갔더니 알바생이 안 보였다. 부르자 매장 안쪽에서 나왔다."

시뮬레이션에서 바꾸는 것:
- 증언 "최유나: 서지훈은 계속 카운터에 있었다"(서지훈 -0.3) 삭제
- 증언 "최유나: 2시 24분 카운터에 알바생이 없었고 매장 안쪽에서 나왔다"(서지훈 +W_ABSENT) 추가
- 카운터#1 POS(02:19·02:24) 서지훈 무게 -0.4 → B1_SJ (5분 빈틈을 말로 메워 줄 사람이 없어짐)
- 정문 목격 소거: 서지훈 -0.4 → FRONT_SJ, 최유나 -0.4 → FRONT_CY (서로 못 봤으므로 약해짐, 정문 종소리는 남음)
"""
import random, sys, copy
sys.stdout.reconfigure(encoding="utf-8")
import sim_tutorial as s
SJ, JM, CY, OH = s.R
S1_0, TESTI_0 = copy.deepcopy(s.S1), list(s.TESTI)
ORIG = s.pressure
CFG = {}


def patched(k, stage, variant, said, jit):
    p = ORIG(k, stage, variant, said, jit)
    if "FRONT_SJ" in CFG and said["front"] and {"A2", "A6"} <= k:
        p[SJ] += .4 + CFG["FRONT_SJ"]   # 원래 -0.4를 FRONT_SJ로
        p[CY] += .4 + CFG["FRONT_CY"]
    if CFG.get("elim") and {"A2", "A6"} <= k:
        for r in (SJ, CY, OH):
            p[r] -= .8
    return p


s.pressure = patched


def setup(cfg):
    s.S1.clear(); s.S1.update(copy.deepcopy(S1_0)); s.TESTI[:] = list(TESTI_0); CFG.clear()
    if not cfg:
        return
    CFG.update(cfg)
    s.TESTI[:] = [t for t in s.TESTI if not t[4].startswith("최유나: 서지훈은 계속 카운터에 있었다")]
    s.TESTI.append((CY, SJ, cfg["W_ABSENT"], 1, "최유나: 2시 24분 카운터에 알바생이 없었고 매장 안쪽에서 나왔다"))
    own, place, w = s.S1["B1"]
    s.S1["B1"] = (own, place, {SJ: cfg["B1_SJ"]})


def go(name, cfg, n=20000):
    out = []
    for elim in (False, True):
        setup(cfg)
        CFG["elim"] = elim
        random.seed(5)
        res = [s.run(policy="strategic", noise=.2) for _ in range(n)]
        a = [x for x in res if x["action"]]
        second, close = {r: 0 for r in s.R}, 0
        for x in res:
            p = x["p2"]
            o = sorted(((v, r) for r, v in p.items() if r != JM), reverse=True)
            second[o[0][1]] += 1
            close += p[JM] - o[0][0] < 1.0
        out.append((s.top_rates(res, "p1"), s.top_rates(res, "p2"), s.top_rates(a, "p2")[JM] / len(a), second, close / n))
    f = lambda t: " ".join(f"{r} {t[r]/n*100:.0f}%" for r in s.R)
    print(f"[{name}]")
    print(f"  1차 끝 1위: {f(out[0][0])}")
    print(f"  2차 끝 1위: {f(out[0][1])} | 1점 미만 접전 {out[0][4]*100:.0f}%")
    print(f"  소거 추리 해냄 2차 끝: {f(out[1][1])} | 액션 쓴 판 정민재 {out[1][2]*100:.0f}%")


if __name__ == "__main__":
    go("현재(30장 정본)", None)
    go("제안안(기본 무게)", dict(W_ABSENT=.3, B1_SJ=-.2, FRONT_SJ=-.2, FRONT_CY=-.3))
    go("제안안, 빈틈 약하게", dict(W_ABSENT=.2, B1_SJ=-.3, FRONT_SJ=-.3, FRONT_CY=-.35))
    go("제안안, 빈틈 세게", dict(W_ABSENT=.5, B1_SJ=0, FRONT_SJ=-.1, FRONT_CY=-.2))
