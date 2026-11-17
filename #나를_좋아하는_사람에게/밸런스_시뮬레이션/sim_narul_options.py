"""밸런스 조정안 비교 (2026-11-17). 정본 sim_narul.py 를 불러와 무게만 바꿔 본다. 정본은 실제 적용 뒤에만 바꾼다."""
import random, sys, copy, statistics as st
sys.stdout.reconfigure(encoding="utf-8")
import sim_narul as s
BASE = (copy.deepcopy(s.CLUES), copy.deepcopy(s.COMBOS), copy.deepcopy(s.TESTIMONY), copy.deepcopy(s.STAGE_MULT))


def reset():
    s.CLUES, s.COMBOS, s.TESTIMONY, s.STAGE_MULT = [copy.deepcopy(x) for x in BASE]


def run_opt(name, n=10000, noise=.2):
    random.seed(11)
    res = [s.run("strategic", noise=noise) for _ in range(n)]
    out = []
    for si in (0, 1, 2):
        t = s.top_rates([x["snaps"][si]["pe"] for x in res])
        out.append(" ".join(f"{r[:1]}{t[r]/n*100:.0f}" for r in s.R))
    close = sum(1 for x in res if (lambda p: p[s.CULPRIT] - max(v for r, v in p.items() if r != s.CULPRIT) < 1)(x["snaps"][-1]["pe"])) / n
    print(f"{name:<34} | 1단계 {out[0]} | 2단계 {out[1]} | 3단계 {out[2]} | 마지막 1점 미만 {close*100:.0f}%")


def setw(code, w):
    v = s.CLUES[code]; s.CLUES[code] = (v[0], v[1], v[2], w)


if __name__ == "__main__":
    print("(무게 ±20%, 소거 추리 포함. 박=박혜수 정=정형미 유=유정석 노=노형철 정=정준희 순)")
    reset(); run_opt("현재")
    reset(); setw("G2", {s.JH: .7}); run_opt("A. G2 약하게(1.5→0.7)")
    reset(); setw("D2", {s.JH: .7, s.PH: .5}); run_opt("B. D2 약하게(정형미 1.5→0.7)")
    reset(); setw("G2", {s.JH: .7}); setw("D2", {s.JH: .7, s.PH: .5}); s.COMBOS = [c for c in s.COMBOS if c[0] != {"D2", "G2"}]; run_opt("C. A+B, D2+G2 짝 없앰")
    reset(); s.TESTIMONY.append((None, s.NH, 1.0, 1.0, set(), 2, "조사 3단계 노형철 쪽 의심거리 +1.0")); run_opt("D. 조사 3단계 노형철 +1.0")
    reset(); setw("G2", {s.JH: .7}); setw("D2", {s.JH: .7, s.PH: .5}); s.COMBOS = [c for c in s.COMBOS if c[0] != {"D2", "G2"}]
    s.TESTIMONY.append((None, s.NH, 1.0, 1.0, set(), 2, "노형철 +1.0")); run_opt("E. C+D")
    reset(); s.STAGE_MULT[1] = dict(s.STAGE_MULT[1], J1=1.0); s.STAGE_MULT[2] = s.STAGE_MULT[1]; run_opt("F. J1 2단계 재해석 없음")
