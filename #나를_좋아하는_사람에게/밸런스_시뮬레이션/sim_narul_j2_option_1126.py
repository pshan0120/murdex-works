"""2026-11-26 J2 문구 가 안(표지에 "2013"만, "고충 상담 기록"이라는 말 없음)의 예상치.
J2 혼자 0.3, A15·W2와 셋이 모여야 0.5(W2 노트북의 2013년 고충 상담 기록과 맞춰야 뜻이 섬).
실행: python sim_narul_j2_option_1126.py
"""
import random
import sim_narul as S

S.CLUES["J2"] = (0, "NOT:" + S.JH, False, {S.JH: .3})
S.COMBOS[:] = [c for c in S.COMBOS if c[0] != {"A15", "J2"}] + [({"A15", "J2", "W2"}, S.JH, .5, 0)]
random.seed(11)
S.report("J2 가 안", n=20000, policy="strategic")
