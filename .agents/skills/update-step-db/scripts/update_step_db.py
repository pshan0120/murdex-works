import sys
import os
import re
import argparse

# murdex-api 경로를 sys.path에 추가하여 SharedConnectionPool 사용
api_dir = r"c:\dev\KLIEN\murdex\murdex-api"
if api_dir not in sys.path:
    sys.path.insert(0, api_dir)

try:
    from infrastructure.database.shared_connection_pool import SharedConnectionPool
except ImportError:
    print(f"[ERROR] murdex-api 모듈을 불러올 수 없습니다. 경로를 확인하세요: {api_dir}")
    sys.exit(1)

sys.stdout.reconfigure(encoding='utf-8')

def parse_step_file(file_path):
    """
    단계_*.txt 파일을 읽어 StepID, 단계 이름, 단계 설명(HTML)을 추출합니다.
    """
    if not os.path.exists(file_path):
        print(f"[ERROR] 파일을 찾을 수 없습니다: {file_path}")
        return None

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(file_path, "r", encoding="utf-8-sig") as f:
            content = f.read()

    # StepID 추출
    step_id_match = re.search(r'StepID\s*:\s*([a-fA-F0-9\-]+)', content)
    if not step_id_match:
        print(f"[SKIP] StepID를 찾을 수 없음: {os.path.basename(file_path)}")
        return None
    step_id = step_id_match.group(1).strip()

    # 단계 이름 추출 (2. 단계 이름 아래 줄)
    name_match = re.search(r'2\.\s*단계\s*이름\s*\n+([^\n]+)', content)
    step_name = name_match.group(1).strip() if name_match else None

    # 단계 설명 (HTML) 추출
    # "단계 설명" 또는 "7. 단계 설명" 또는 "8. 단계 설명" 이후의 <div class="story-content">...</div> 블록 탐색
    description = None
    desc_start_match = re.search(r'(?:단계\s*설명|\d+\.\s*단계\s*설명)\s*\n+(<div class="story-content".*)', content, re.DOTALL)
    if desc_start_match:
        html_candidate = desc_start_match.group(1).strip()
        # <div class="story-content">부터 매칭되는 최외곽 </div>까지 추출
        div_count = 0
        end_idx = 0
        in_div = False
        lines = html_candidate.split('\n')
        extracted_lines = []
        for line in lines:
            extracted_lines.append(line)
            div_count += line.count('<div') - line.count('</div>')
            if line.count('<div') > 0:
                in_div = True
            if in_div and div_count <= 0:
                break
        description = "\n".join(extracted_lines).strip()

    if not description:
        print(f"[WARNING] 단계 설명 HTML 영역을 찾지 못함: {os.path.basename(file_path)}")
        return None

    return {
        "step_id": step_id,
        "step_name": step_name,
        "description": description,
        "file_name": os.path.basename(file_path)
    }

def update_step_db(target_path, dry_run=False):
    target_files = []
    abs_path = os.path.abspath(target_path)

    if os.path.isfile(abs_path):
        target_files.append(abs_path)
    elif os.path.isdir(abs_path):
        for root, _, files in os.walk(abs_path):
            for file in sorted(files):
                if file.startswith("단계_") and file.endswith(".txt"):
                    target_files.append(os.path.join(root, file))

    if not target_files:
        print(f"[ERROR] 처리할 대상 단계_*.txt 파일이 없습니다: {target_path}")
        return

    parsed_steps = []
    for fpath in target_files:
        parsed = parse_step_file(fpath)
        if parsed:
            parsed_steps.append(parsed)

    if not parsed_steps:
        print("[ERROR] 파싱된 단계 정보가 없습니다.")
        return

    print(f"[INFO] 총 {len(parsed_steps)}개의 단계 정보를 파싱했습니다.")
    print("-" * 70)

    if dry_run:
        print("[DRY-RUN] DB 업데이트 없이 파싱 결과만 출력합니다:")
        for s in parsed_steps:
            print(f" - 파일: {s['file_name']}")
            print(f"   StepID: {s['step_id']}")
            print(f"   단계 이름: {s['step_name']}")
            print(f"   설명 길이: {len(s['description'])} 자")
            print(f"   설명 미리보기: {s['description'][:80]}...")
            print()
        print("[DRY-RUN] 검증 완료.")
        return

    pool = SharedConnectionPool.get_instance()
    updated_count = 0

    with pool.get_connection() as conn:
        cursor = conn.cursor()
        for s in parsed_steps:
            sql = """
                UPDATE story_step
                SET description = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE step_id = %s
            """
            cursor.execute(sql, (s["description"], s["step_id"]))
            if cursor.rowcount > 0:
                updated_count += 1
                print(f"[SUCCESS] {s['file_name']} (StepID: {s['step_id']}) -> description 업데이트 완료")
            else:
                print(f"[WARNING] {s['file_name']} (StepID: {s['step_id']}) -> DB 일치 행 없음 (업데이트 실패/변화 없음)")
        conn.commit()

    print("-" * 70)
    print(f"[DONE] 총 {updated_count}/{len(parsed_steps)}개 단계의 description이 DB에 성공적으로 업데이트되었습니다.")

def main():
    parser = argparse.ArgumentParser(description="단계_*.txt 파일의 '단계 설명' HTML을 MySQL story_step DB 테이블에 업데이트합니다.")
    parser.add_argument("target_path", help="단계 텍스트 파일 또는 단계 파일들이 포함된 디렉토리 경로")
    parser.add_argument("--dry-run", action="store_true", help="실제 DB 업데이트 없이 파싱 결과만 확인")
    args = parser.parse_args()

    update_step_db(args.target_path, dry_run=args.dry_run)

if __name__ == "__main__":
    main()
