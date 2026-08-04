import sys
import os
import re
import uuid
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


def extract_top_level_divs(text: str) -> list[str]:
    """
    HTML 텍스트에서 <div class="story-content">...</div> 블록들을
    중첩 뎁스(depth)를 감안하여 최상위 블록 단위로 올바르게 분리합니다.
    """
    divs = []
    pos = 0
    start_tag = '<div class="story-content">'

    while True:
        start_idx = text.find(start_tag, pos)
        if start_idx == -1:
            break

        depth = 0
        curr = start_idx
        end_idx = -1

        while curr < len(text):
            next_open = text.find('<div', curr)
            next_close = text.find('</div>', curr)

            if next_close == -1:
                break

            if next_open != -1 and next_open < next_close:
                depth += 1
                curr = next_open + 4
            else:
                depth -= 1
                curr = next_close + 6
                if depth == 0:
                    end_idx = curr
                    break

        if end_idx != -1:
            divs.append(text[start_idx:end_idx].strip())
            pos = end_idx
        else:
            pos = start_idx + len(start_tag)

    return divs


def parse_question_file(file_path: str) -> list[dict]:
    """
    QuestionID가 작성된 질문 텍스트 파일을 파싱하여 질문 및 선택지 블록을 반환합니다.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    cleaned_text = remove_html_comments(raw_text)

    # QuestionID 패턴으로 분할 (e.g. QuestionID : UUID 또는 QuestionID: UUID)
    qid_pattern = r'(?:QuestionID\s*:\s*([a-f0-9\-]{36}))'
    matches = list(re.finditer(qid_pattern, cleaned_text, flags=re.IGNORECASE))

    if not matches:
        print("[WARN] 파일에서 QuestionID 패턴을 찾지 못했습니다. --inject 옵션으로 QuestionID를 먼저 주입해 주세요.")
        return []

    blocks = []
    for i, match in enumerate(matches):
        qid = match.group(1)
        start_idx = match.end()
        end_idx = matches[i+1].start() if i + 1 < len(matches) else len(cleaned_text)

        block_text = cleaned_text[start_idx:end_idx]

        # [질문] 및 [선택지] 위치 파악
        q_pos = block_text.find("[질문]")
        opt_pos = block_text.find("[선택지]")

        if q_pos == -1 or opt_pos == -1:
            divs = extract_top_level_divs(block_text)
            if not divs:
                continue
            question_title = divs[0]
            options = divs[1:]
        else:
            q_part = block_text[q_pos:opt_pos]
            opt_part = block_text[opt_pos:]

            q_divs = extract_top_level_divs(q_part)
            opt_divs = extract_top_level_divs(opt_part)

            question_title = q_divs[0] if q_divs else ""
            options = opt_divs

        blocks.append({
            "question_id": qid,
            "question_title": question_title,
            "options": options
        })

    return blocks


def update_db(blocks: list[dict], dry_run: bool = False):
    """
    파싱된 질문 및 선택지 블록을 DB(question, question_option)에 업데이트합니다.
    """
    if not blocks:
        print("[INFO] 업데이트할 블록이 없습니다.")
        return

    pool = SharedConnectionPool()
    with pool.get_connection() as conn:
        cursor = conn.cursor(dictionary=True)

        updated_q_count = 0
        updated_opt_count = 0

        for b in blocks:
            qid = b["question_id"]
            q_title = b["question_title"]
            options = b["options"]

            if dry_run:
                print(f"[DRY-RUN] QuestionID: {qid}")
                print(f"  - 질문 Title:\n{q_title[:100]}...")
                print(f"  - 선택지 개수: {len(options)}")
                for idx, opt in enumerate(options, 1):
                    print(f"    [{idx}] {opt[:60]}...")
                print("-" * 50)
                continue

            # 1. Question Title 업데이트
            cursor.execute(
                "UPDATE question SET title = %s, updated_at = CURRENT_TIMESTAMP WHERE question_id = %s",
                (q_title, qid)
            )
            if cursor.rowcount > 0:
                updated_q_count += 1

            # 2. 기존 Question Options 가져오기
            cursor.execute(
                "SELECT option_id, option_order FROM question_option WHERE question_id = %s ORDER BY option_order",
                (qid,)
            )
            existing_options = cursor.fetchall()

            for idx, opt_text in enumerate(options):
                opt_order = idx + 1
                if idx < len(existing_options):
                    # 기존 옵션 UPDATE
                    existing_opt_id = existing_options[idx]["option_id"]
                    cursor.execute(
                        "UPDATE question_option SET option_text = %s, option_order = %s WHERE option_id = %s",
                        (opt_text, opt_order, existing_opt_id)
                    )
                    updated_opt_count += 1
                else:
                    # 신규 옵션 INSERT
                    new_opt_id = str(uuid.uuid4())
                    cursor.execute(
                        "INSERT INTO question_option (option_id, question_id, option_text, option_order) VALUES (%s, %s, %s, %s)",
                        (new_opt_id, qid, opt_text, opt_order)
                    )
                    updated_opt_count += 1

        if not dry_run:
            conn.commit()
            print(f"[DONE] 총 {updated_q_count}개 질문 및 {updated_opt_count}개 선택지가 성공적으로 DB에 업데이트되었습니다.")


def inject_ids_to_file(file_path: str, dry_run: bool = False):
    """
    기존 질문 파일에서 질문/선택지 블록을 파싱하고 DB의 QuestionID를 매칭하여 문서를 주입/재작성합니다.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    pool = SharedConnectionPool()
    with pool.get_connection() as conn:
        cursor = conn.cursor(dictionary=True)

        cursor.execute('''
            SELECT q.question_id, q.title, q.question_order, r.character_name, r.role_name
            FROM question q
            JOIN story_step step ON q.step_id = step.step_id
            JOIN story st ON step.story_id = st.story_id
            LEFT JOIN role r ON q.role_id = r.role_id
            WHERE st.title LIKE '%바스타즈%'
            ORDER BY q.question_order, r.role_name
        ''')
        db_questions = cursor.fetchall()

    char_q_map = {}
    common_q_map = {}
    for q in db_questions:
        if q["character_name"]:
            char_q_map[q["character_name"]] = q["question_id"]
            if q["role_name"]:
                char_q_map[q["role_name"]] = q["question_id"]
        else:
            common_q_map[q["question_order"]] = q["question_id"]

    print(f"[INFO] DB 매핑 생성 완료 (개별 질문: {len(char_q_map)}개, 공통 질문: {len(common_q_map)}개)")

    lines = content.splitlines()
    new_lines = []
    current_char = None
    current_question_order = None

    i = 0
    while i < len(lines):
        line = lines[i]

        # 섹션 헤더 감지 (예: ## 1. 스컬크러셔, ## 2. 엘드리치)
        header_match = re.search(r'##\s*\d+\.\s*([가-힣a-zA-Z]+)', line)
        if header_match:
            current_char = header_match.group(1).strip()

        # 공통 질문 헤더 감지 (예: // 첫 번째 질문, // 두 번째 질문, section-title: 1. 처형 대상...)
        if "1. 처형 대상" in line:
            current_question_order = 2
        elif "2. 최종 전투" in line:
            current_question_order = 3

        # 질문 시작 감지 (<div class="story-content"> 다음 <div class="section-title">가 포함된 경우)
        if line.strip() == '<div class="story-content">' and i + 1 < len(lines) and '<div class="section-title">' in lines[i+1]:
            # 해당하는 QuestionID 찾기
            target_qid = None
            if current_char and current_char in char_q_map:
                target_qid = char_q_map[current_char]
            elif current_question_order and current_question_order in common_q_map:
                target_qid = common_q_map[current_question_order]

            if target_qid:
                new_lines.append(f"QuestionID : {target_qid}")
                new_lines.append("[질문]")

            # 질문 div 추출
            q_div = []
            while i < len(lines):
                q_div.append(lines[i])
                if lines[i].strip() == '</div>':
                    i += 1
                    break
                i += 1

            new_lines.extend(q_div)
            new_lines.append("")
            new_lines.append("[선택지]")

            # 질문 직후 나오는 연속된 <div class="story-content"> 선택지들 처리
            while i < len(lines):
                # 빈 줄이나 주석, 기타 설명텍스트인 경우 건너뛰기 전 확인
                stripped = lines[i].strip()
                if stripped == '<div class="story-content">':
                    opt_div = []
                    while i < len(lines):
                        opt_div.append(lines[i])
                        if lines[i].strip() == '</div>':
                            i += 1
                            break
                        i += 1
                    new_lines.extend(opt_div)
                    new_lines.append("")
                elif stripped.startswith('//') or stripped == '':
                    i += 1
                else:
                    break
            continue

        new_lines.append(line)
        i += 1

    result_text = "\n".join(new_lines)

    if dry_run:
        print("[DRY-RUN] 주입 결과 미리보기:")
        print(result_text[:500])
    else:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(result_text)
        print(f"[SUCCESS] {file_path} 문서에 QuestionID 및 [질문], [선택지] 주입이 완료되었습니다.")


def main():
    parser = argparse.ArgumentParser(description="질문 텍스트 파일(질문_개별.txt, 질문_공통.txt)의 변경 사항을 MySQL DB에 업데이트합니다.")
    parser.add_argument("file_path", help="질문 텍스트 파일 경로")
    parser.add_argument("--dry-run", action="store_true", help="DB를 변경하지 않고 파싱 결과만 출력합니다.")
    parser.add_argument("--inject", action="store_true", help="문서에 DB의 QuestionID 및 [질문], [선택지] 라벨을 주입합니다.")

    args = parser.parse_args()

    if not os.path.exists(args.file_path):
        print(f"[ERROR] 파일이 존재하지 않습니다: {args.file_path}")
        sys.exit(1)

    if args.inject:
        inject_ids_to_file(args.file_path, dry_run=args.dry_run)
    else:
        blocks = parse_question_file(args.file_path)
        update_db(blocks, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
