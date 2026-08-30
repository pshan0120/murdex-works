"""
27차 피드백 대응: 단계 11(통합 조사)의 예상 소요 시간을 60분 -> 50분으로 조정.
이 단계는 is_auto_proceed=N(자동 진행 없음, NEXT 버튼으로 수동 종료)이라 estimated_duration은
어디까지나 안내용 숫자이고 실제 하드 타임리밋은 아님. 그래서 "필요하면 10분 정도 늘려도 된다"는
안내는 별도 타이머 로직 없이 단계 설명 HTML에 짧은 문구로만 덧붙인다.

실행 전 현재 값을 출력하고, 실행 후 반영 결과를 다시 조회해서 확인한다.
"""
import sys

murdex_api_path = r"c:\dev\KLIEN\murdex\murdex-api"
if murdex_api_path not in sys.path:
    sys.path.append(murdex_api_path)

from infrastructure.database.shared_connection_pool import SharedConnectionPool

STEP_ID = "e84d3e8e-cf80-4744-8f05-218a77bec0ba"
OLD_DESC_SNIPPET = "이제부터는 개별적인 밀담 없이 진행되는 <strong>통합 조사 단계</strong>입니다. 계속해서 조사를 진행하며, 지금까지 수집된 단서와 정보들을 모두와 함께 종합하여 진실을 밝혀낼 시간입니다."
NEW_DESC_SNIPPET = "이제부터는 개별적인 밀담 없이 진행되는 <strong>통합 조사 단계</strong>입니다. 계속해서 조사를 진행하며, 지금까지 수집된 단서와 정보들을 모두와 함께 종합하여 진실을 밝혀낼 시간입니다. 예상 소요 시간은 <strong>50분</strong>이며, 논의가 더 필요하면 10분 정도 유동적으로 늘려서 진행해도 좋습니다."


def main():
    pool = SharedConnectionPool.get_instance()

    with pool.get_connection() as conn:
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT step_id, estimated_duration, description FROM story_step WHERE step_id = %s",
            (STEP_ID,)
        )
        row = cursor.fetchone()
        if not row:
            print(f"StepID {STEP_ID}를 찾을 수 없습니다.")
            return

        print(f"[변경 전] estimated_duration = {row['estimated_duration']}")

        if OLD_DESC_SNIPPET not in row['description']:
            print("경고: description에서 기대한 문구를 찾지 못했습니다. description은 건드리지 않고 estimated_duration만 반영합니다.")
            new_description = row['description']
        else:
            new_description = row['description'].replace(OLD_DESC_SNIPPET, NEW_DESC_SNIPPET)

        cursor.execute(
            "UPDATE story_step SET estimated_duration = %s, description = %s WHERE step_id = %s",
            (50, new_description, STEP_ID)
        )
        conn.commit()

        cursor.execute(
            "SELECT estimated_duration, description FROM story_step WHERE step_id = %s",
            (STEP_ID,)
        )
        updated = cursor.fetchone()
        print(f"[변경 후] estimated_duration = {updated['estimated_duration']}")
        print("[변경 후] description snippet 포함 여부:", NEW_DESC_SNIPPET in updated['description'])


if __name__ == "__main__":
    main()
