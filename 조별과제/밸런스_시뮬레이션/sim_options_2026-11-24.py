"""대응안 비교: 강의실#4의 비품창고 언급을 덜어 냈을 때 (2026-11-24)

정본(sim_jobyeolgwaje.py)을 불러와 설정만 바꿔 돌린다. 정본은 실제로 적용한 뒤에만 고친다.

  A안: 강의실#4에서 "창밖으로 비품 창고가 보인다"만 덜어 낸다.
       비품창고 입구#1에는 "2층 창문에서도 창고를 오가는 모습이 보일 만한 위치"가 그대로 남아,
       창고 쪽을 파고들면 창문과의 고리는 여전히 성립한다.
  B안: A안에 더해 비품창고 입구#1의 그 문장까지 덜어 낸다. 창문과 창고를 잇는 고리가 사라진다.

실행: python sim_options_2026-11-24.py
"""
import random, sys
sys.stdout.reconfigure(encoding="utf-8")
import sim_jobyeolgwaje as S

LEE = S.LEE
BASE_W = dict(S.C["강의실4"]["w"])
BASE_COMBOS = list(S.COMBOS)
BASE_PATHS = dict(S.PATHS)


def restore():
    S.C["강의실4"]["w"] = dict(BASE_W)
    S.COMBOS[:] = BASE_COMBOS
    S.PATHS.clear(); S.PATHS.update(BASE_PATHS)


def apply_a():
    """창문 자체는 침입 경로를 떠올리게 하므로 약한 무게만 남긴다.
    창고와의 고리는 비품창고 입구#1이 대신 이어 주므로, 짝의 조건을 그쪽으로 옮긴다."""
    restore()
    S.C["강의실4"]["w"] = {LEE: .1}
    S.COMBOS[:] = [({"창고내부1", "창고입구1"} if req == {"창고내부1", "강의실4"} else req, r, w, s)
                   for req, r, w, s in BASE_COMBOS]
    S.PATHS["사다리와 창문"] = ({"창고내부1", "창고입구1"}, False)


def apply_b():
    """창문과 창고를 잇는 문장을 양쪽에서 모두 덜어 낸 경우."""
    restore()
    S.C["강의실4"]["w"] = {LEE: .1}
    S.COMBOS[:] = [x for x in BASE_COMBOS if x[0] != {"창고내부1", "강의실4"}]
    S.PATHS["사다리와 창문"] = ({"창고내부1"}, False)


if __name__ == "__main__":
    for name, fn in [("지금 그대로", restore), ("A안: 강의실#4에서만 뺌", apply_a),
                     ("B안: 창고 입구#1에서도 뺌", apply_b)]:
        fn()
        random.seed(1)
        S.report(name, policy="strategic")
    restore()
