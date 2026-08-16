import sys
import os
import re
import argparse

sys.stdout.reconfigure(encoding='utf-8')

# Add murdex-api to path to use shared_connection_pool
murdex_api_path = r"c:\dev\KLIEN\murdex\murdex-api"
if murdex_api_path not in sys.path:
    sys.path.append(murdex_api_path)

try:
    from infrastructure.database.shared_connection_pool import SharedConnectionPool
except ImportError:
    print("Error: Could not import SharedConnectionPool. Ensure murdex-api path is correct and dependencies are installed.")
    sys.exit(1)


def remove_html_comments(text: str) -> str:
    """HTML 주석(<!-- ... -->)을 제거합니다."""
    return re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)


def parse_ending_file(file_path: str) -> list[dict]:
    """
    엔딩_개별.txt 파일을 파싱하여 엔딩 블록 목록을 반환합니다.

    각 블록은 다음 키를 포함합니다:
      - title: 제목
      - ending_id: EndingID UUID
      - content: ending_story에 들어갈 HTML 문자열
    """
    with open(file_path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    # HTML 주석 제거 (<!-- ... -->)
    cleaned_text = remove_html_comments(raw_text)

    # 빈 줄이 두 개 이상인 경우 단일 빈 줄로 정리
    cleaned_lines = cleaned_text.splitlines()

    blocks = []
    current_block = None
    in_content_section = False
    content_lines = []

    for line in cleaned_lines:
        stripped = line.rstrip()

        # 새 블록 시작
        if stripped.startswith("제목:"):
            # 이전 블록 저장
            if current_block is not None:
                current_block["content"] = _finalize_content(content_lines)
                blocks.append(current_block)

            title = stripped.replace("제목:", "").strip()
            current_block = {"title": title, "ending_id": None, "content": ""}
            in_content_section = False
            content_lines = []

        elif current_block is not None:
            if stripped.startswith("EndingID :"):
                current_block["ending_id"] = stripped.replace("EndingID :", "").strip()

            elif stripped.startswith("내용:"):
                in_content_section = True

            elif in_content_section:
                content_lines.append(line.rstrip())

    # 마지막 블록 저장
    if current_block is not None:
        current_block["content"] = _finalize_content(content_lines)
        blocks.append(current_block)

    return blocks


def _finalize_content(content_lines: list[str]) -> str:
    """수집된 내용 줄들을 정리하여 최종 HTML 문자열로 변환합니다."""
    # 앞뒤 빈 줄 제거
    while content_lines and not content_lines[0].strip():
        content_lines.pop(0)
    while content_lines and not content_lines[-1].strip():
        content_lines.pop()

    return "\n".join(content_lines)


def update_db(blocks: list[dict], target_ids: list[str] = None, dry_run: bool = False) -> tuple[int, int]:
    """
    파싱된 블록들을 DB에 업데이트합니다.

    Returns:
        (성공 건수, 전체 건수)
    """
    valid_blocks = [b for b in blocks if b.get("ending_id") and b.get("content")]

    if target_ids:
        target_set = set(target_ids)
        valid_blocks = [b for b in valid_blocks if b["ending_id"] in target_set]

    if dry_run:
        print(f"\n[DRY RUN] 파싱된 엔딩 블록: {len(blocks)}개 (선택/유효: {len(valid_blocks)}개)\n")
        for idx, block in enumerate(valid_blocks, 1):
            content_snippet = block["content"][:60].replace("\n", " ")
            if len(block["content"]) > 60:
                content_snippet += "..."
            print(f"  [{idx:02d}] {block['title']}")
            print(f"        EndingID : {block['ending_id']}")
            print(f"        내용 미리보기 : {content_snippet}")
            print()
        return len(valid_blocks), len(valid_blocks)

    pool = SharedConnectionPool.get_instance()
    success_count = 0

    with pool.get_connection() as conn:
        cursor = conn.cursor()

        for block in valid_blocks:
            ending_id = block["ending_id"]
            ending_name = block["title"]
            ending_story = block["content"]

            try:
                cursor.execute("SELECT 1 FROM story_ending WHERE ending_id = %s", (ending_id,))
                if not cursor.fetchone():
                    print(f"  [WARNING] 매칭된 행 없음 - EndingID: {ending_id} ({ending_name})")
                else:
                    cursor.execute(
                        "UPDATE story_ending SET ending_name = %s, ending_story = %s WHERE ending_id = %s",
                        (ending_name, ending_story, ending_id)
                    )
                    success_count += 1

            except Exception as e:
                print(f"  [ERROR] 업데이트 실패 - EndingID: {ending_id} ({ending_name}): {e}")

        conn.commit()

    return success_count, len(valid_blocks)


def main():
    parser = argparse.ArgumentParser(
        description="엔딩 텍스트 파일(엔딩_개별.txt)의 변경 사항을 MySQL DB에 업데이트합니다."
    )
    parser.add_argument("file_path", help="엔딩 텍스트 파일 경로 (예: 엔딩_개별.txt)")
    parser.add_argument(
        "--ending-ids", "-i",
        nargs="+",
        help="업데이트할 특정 EndingID 목록 (공백으로 구분)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="DB를 변경하지 않고 파싱 결과만 출력합니다."
    )
    args = parser.parse_args()

    if not os.path.exists(args.file_path):
        print(f"[ERROR] 파일을 찾을 수 없습니다: {args.file_path}")
        sys.exit(1)

    print(f"파싱 중: {args.file_path} ...")
    blocks = parse_ending_file(args.file_path)
    print(f"발견된 전체 블록 수: {len(blocks)}개")

    if args.dry_run:
        update_db(blocks, target_ids=args.ending_ids, dry_run=True)
    else:
        print("DB 업데이트 중...")
        success, total = update_db(blocks, target_ids=args.ending_ids, dry_run=False)
        print(f"\n완료. {total}개 중 {success}개 업데이트 성공.")


if __name__ == "__main__":
    main()
