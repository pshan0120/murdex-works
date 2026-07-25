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

def extract_div_block(content, start_pattern):
    """지정된 정규표현식 패턴 이후에 나타나는 첫 <div class="story-content"> 블록을 끝까지 추출합니다."""
    match = re.search(start_pattern + r'\s*\n+(<div class="story-content".*)', content, re.DOTALL)
    if not match:
        return None
    
    html_candidate = match.group(1).strip()
    div_count = 0
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
            
    return "\n".join(extracted_lines).strip()

def parse_role_file(file_path):
    if not os.path.exists(file_path):
        print(f"[ERROR] 파일을 찾을 수 없습니다: {file_path}")
        return None

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(file_path, "r", encoding="utf-8-sig") as f:
            content = f.read()

    # RoleID 추출
    role_id_match = re.search(r'RoleID\s*:\s*([a-fA-F0-9\-]+)', content)
    if not role_id_match:
        print(f"[SKIP] RoleID를 찾을 수 없음: {os.path.basename(file_path)}")
        return None
    role_id = role_id_match.group(1).strip()

    # 역할 이름 추출
    name_match = re.search(r'1\.\s*역할\s*이름\s*\n+([^\n]+)', content)
    role_name = name_match.group(1).strip() if name_match else None

    # 공개 정보 추출
    public_info = extract_div_block(content, r'(?:6\.\s*공개\s*정보|공개\s*정보)')
    
    # 역할 시트 (상세 정보) 추출
    description = extract_div_block(content, r'(?:7\.\s*역할\s*시트|상세\s*정보|역할\s*시트)')

    if not public_info and not description:
        print(f"[WARNING] 공개 정보와 역할 시트를 모두 찾지 못함: {os.path.basename(file_path)}")
        return None

    return {
        "role_id": role_id,
        "role_name": role_name,
        "public_info": public_info,
        "description": description,
        "file_name": os.path.basename(file_path)
    }

def update_role_db(target_path, dry_run=False):
    target_files = []
    abs_path = os.path.abspath(target_path)

    if os.path.isfile(abs_path):
        target_files.append(abs_path)
    elif os.path.isdir(abs_path):
        for root, _, files in os.walk(abs_path):
            for file in sorted(files):
                if file.startswith("역할_") and file.endswith(".txt"):
                    target_files.append(os.path.join(root, file))

    if not target_files:
        print(f"[ERROR] 처리할 대상 역할_*.txt 파일이 없습니다: {target_path}")
        return

    parsed_roles = []
    for fpath in target_files:
        parsed = parse_role_file(fpath)
        if parsed:
            parsed_roles.append(parsed)

    if not parsed_roles:
        print("[ERROR] 파싱된 역할 정보가 없습니다.")
        return

    print(f"[INFO] 총 {len(parsed_roles)}개의 역할 정보를 파싱했습니다.")
    print("-" * 70)

    if dry_run:
        print("[DRY-RUN] DB 업데이트 없이 파싱 결과만 출력합니다:")
        for pr in parsed_roles:
            print(f" - 파일: {pr['file_name']}")
            print(f"   RoleID: {pr['role_id']}")
            print(f"   역할 이름: {pr['role_name']}")
            if pr['public_info']:
                print(f"   공개 정보 길이: {len(pr['public_info'])} 자")
            else:
                print(f"   공개 정보: 없음")
            if pr['description']:
                print(f"   상세 정보 길이: {len(pr['description'])} 자")
            else:
                print(f"   상세 정보: 없음")
            print()
        print("[DRY-RUN] 검증 완료.")
        return

    # DB 업데이트 수행
    pool = SharedConnectionPool.get_instance()
    success_count = 0
    fail_count = 0

    with pool.get_connection() as conn:
        cursor = conn.cursor()
        
        for pr in parsed_roles:
            role_id = pr['role_id']
            public_info = pr['public_info']
            description = pr['description']
            file_name = pr['file_name']
            
            # 빌드 쿼리
            updates = []
            params = []
            if public_info is not None:
                updates.append("public_info = %s")
                params.append(public_info)
            if description is not None:
                updates.append("description = %s")
                params.append(description)
                
            if not updates:
                print(f"[SKIP] {file_name}: 업데이트할 내용이 없습니다.")
                continue
                
            query = f"UPDATE role SET {', '.join(updates)} WHERE role_id = %s"
            params.append(role_id)
            
            cursor.execute(query, tuple(params))
            
            if cursor.rowcount > 0:
                updated_fields = "공개 정보, 상세 정보" if len(updates) == 2 else ("공개 정보" if "public_info" in updates[0] else "상세 정보")
                print(f"[SUCCESS] {file_name} (RoleID: {role_id}) -> {updated_fields} 업데이트 완료")
                success_count += 1
            else:
                print(f"[WARNING] {file_name} (RoleID: {role_id}) -> DB 일치 행 없음 (업데이트 실패/변화 없음)")
                fail_count += 1
                
        conn.commit()

    print("-" * 70)
    print(f"[DONE] 총 {success_count}/{len(parsed_roles)}개 역할의 정보가 DB에 성공적으로 업데이트되었습니다.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="역할 텍스트 파일의 HTML을 role 테이블에 업데이트합니다.")
    parser.add_argument("target_path", help="처리할 역할_*.txt 파일 또는 파일이 포함된 디렉토리 경로")
    parser.add_argument("--dry-run", action="store_true", help="DB에 쓰지 않고 파싱 결과만 확인")
    
    args = parser.parse_args()
    update_role_db(args.target_path, dry_run=args.dry_run)
