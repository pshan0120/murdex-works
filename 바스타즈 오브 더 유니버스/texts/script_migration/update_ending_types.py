"""
27차 피드백 대응: 엔딩 타입 라벨링 오류 수정.

기존 문제: #12(바스타즈의 결속, 말리스 처형 + 마신 격퇴)이 TRUE_ENDING이었음.
하지만 말리스는 실제로는 무고했고(진범은 없음, 흑막 엘드리치가 자살로 위장), 이 결말은 그저
"엉뚱한 사람을 처형했지만 그래도 마신은 이겼다"는 점에서 #7~#11(BAD_ENDING)과 기계적으로
동일한 형태임. 반면 #13(새로운 여명, 아무도 처형하지 않고 진실을 전부 밝혀낸 뒤 승리)이야말로
유일하게 "제대로 흑막을 밝혀내고 아무도 억울하게 죽지 않은" 결말이라 TRUE_ENDING에 해당함.

- #12 바스타즈의 결속: TRUE_ENDING -> NORMAL_ENDING
- #13 새로운 여명: HIDDEN_ENDING -> TRUE_ENDING

(#7~#11은 이미 BAD_ENDING이고 제목들도 이미 어두운 톤이라 손대지 않음.)
"""
import sys

murdex_api_path = r"c:\dev\KLIEN\murdex\murdex-api"
if murdex_api_path not in sys.path:
    sys.path.append(murdex_api_path)

from infrastructure.database.shared_connection_pool import SharedConnectionPool

CHANGES = [
    ("ec68b124-b8b3-4058-b159-134c032d178f", "TRUE_ENDING", "NORMAL_ENDING"),  # 12. 바스타즈의 결속
    ("80b95bc2-3e55-463c-af87-354118714861", "HIDDEN_ENDING", "TRUE_ENDING"),  # 13. 새로운 여명
]


def main():
    pool = SharedConnectionPool.get_instance()

    with pool.get_connection() as conn:
        cursor = conn.cursor(dictionary=True)

        for ending_id, expected_old, new_type in CHANGES:
            cursor.execute(
                "SELECT ending_id, ending_type FROM story_ending WHERE ending_id = %s",
                (ending_id,)
            )
            row = cursor.fetchone()
            if not row:
                print(f"NOT FOUND: {ending_id}")
                continue

            print(f"{ending_id}: current={row['ending_type']} (expected {expected_old})")
            if row['ending_type'] != expected_old:
                print("  WARNING: current value does not match expected old value. Skipping to be safe.")
                continue

            cursor.execute(
                "UPDATE story_ending SET ending_type = %s WHERE ending_id = %s",
                (new_type, ending_id)
            )
            print(f"  -> updated to {new_type}")

        conn.commit()

        print("\n[After]")
        for ending_id, _, _ in CHANGES:
            cursor.execute(
                "SELECT ending_id, ending_type FROM story_ending WHERE ending_id = %s",
                (ending_id,)
            )
            row = cursor.fetchone()
            print(f"{ending_id}: {row['ending_type']}")


if __name__ == "__main__":
    main()
