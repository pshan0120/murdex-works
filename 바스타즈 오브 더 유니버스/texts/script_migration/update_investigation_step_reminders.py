"""
27차 피드백 대응: "다음 단계로 넘어가기 전 조 편성" 규칙을 사람들이 깜빡하는 문제.
원인: 이 규칙은 단계 설명(모달) 안 규칙 목록 중간에만 있고, 실제 NEXT/준비완료 버튼은
별개 화면(StepProgress.tsx)에 있어서 조사 시간이 다 지날 때쯤이면 안내를 다시 볼 일이 없었음.

플랫폼에 새로 추가한 story_step.pre_next_reminder 필드(준비완료 버튼 바로 위에 항상 노출됨)에
조사 I/II/IV/V 4개 단계의 조 편성 리마인더를 채워 넣는다.

- 조사 I/II (단계_4, 단계_5): 전원이 협의해서 편성
- 조사 IV/V (단계_8, 단계_9): 엘드리치 플레이어가 편성 (특수 기믹)
"""
import sys

murdex_api_path = r"c:\dev\KLIEN\murdex\murdex-api"
if murdex_api_path not in sys.path:
    sys.path.append(murdex_api_path)

from infrastructure.database.shared_connection_pool import SharedConnectionPool

REMINDER_ALL = "다음 단계로 넘어가기 전에 전원이 협의해서 새로운 조를 편성했는지 확인하세요. 직전 조 편성과 멤버 구성이 겹치면 안 됩니다."
REMINDER_ELDRITCH = "다음 단계로 넘어가기 전에 엘드리치 플레이어가 새로운 조를 편성했는지 확인하세요. 직전 조 편성과 멤버 구성이 겹치면 안 됩니다."

UPDATES = [
    ("7a7c8566-6370-4b7a-89a6-9b05452ca6ec", "조사 I", REMINDER_ALL),
    ("8bfc4c0c-4c3a-48fb-9c7c-7806f6d168f3", "조사 II", REMINDER_ALL),
    ("21aaab99-bc3a-45a3-b876-bc6c9efe3c7c", "조사 IV", REMINDER_ELDRITCH),
    ("ef3364a3-1439-42d5-97bd-012c20ac05b0", "조사 V", REMINDER_ELDRITCH),
]


def main():
    pool = SharedConnectionPool.get_instance()

    with pool.get_connection() as conn:
        cursor = conn.cursor(dictionary=True)

        for step_id, name, reminder in UPDATES:
            cursor.execute(
                "SELECT step_id, step_name, pre_next_reminder FROM story_step WHERE step_id = %s",
                (step_id,)
            )
            row = cursor.fetchone()
            if not row:
                print(f"NOT FOUND: {step_id} ({name})")
                continue
            print(f"{row['step_name']} ({step_id}): before={row['pre_next_reminder']!r}")

            cursor.execute(
                "UPDATE story_step SET pre_next_reminder = %s WHERE step_id = %s",
                (reminder, step_id)
            )

        conn.commit()

        print("\n[After]")
        for step_id, name, _ in UPDATES:
            cursor.execute(
                "SELECT step_name, pre_next_reminder FROM story_step WHERE step_id = %s",
                (step_id,)
            )
            row = cursor.fetchone()
            print(f"{row['step_name']}: {row['pre_next_reminder']}")


if __name__ == "__main__":
    main()
