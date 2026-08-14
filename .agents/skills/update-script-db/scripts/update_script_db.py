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

def fetch_story_roles_and_npcs(cursor, story_id):
    """
    해당 스토리의 role 및 npc_character 목록을 조회합니다.
    """
    cursor.execute("""
        SELECT role_id, character_name, role_name, role_order
        FROM role
        WHERE story_id = %s
        ORDER BY role_order ASC, created_at ASC
    """, (story_id,))
    roles = cursor.fetchall()

    cursor.execute("""
        SELECT npc_id, name
        FROM npc_character
        WHERE story_id = %s
        ORDER BY npc_order ASC, created_at ASC
    """, (story_id,))
    npcs = cursor.fetchall()

    return roles, npcs

def match_role(speaker_str, roles):
    """
    화자 문자열(예: '베일라 (CIA 요원)', '마커스')로 role_id를 탐색합니다.
    """
    if not speaker_str or not roles:
        return None

    clean = speaker_str.strip()
    for r in roles:
        c_name = (r['character_name'] or '').strip()
        r_name = (r['role_name'] or '').strip()
        if c_name and c_name in clean:
            return r['role_id']
        if r_name and r_name in clean:
            return r['role_id']
        if clean in c_name or clean in r_name:
            return r['role_id']
    return None

def match_npc(speaker_str, npcs):
    """
    화자 문자열(예: '클레이')로 npc_id를 탐색합니다.
    """
    if not speaker_str or not npcs:
        return None

    clean = speaker_str.strip()
    for n in npcs:
        n_name = (n['name'] or '').strip()
        if n_name and (n_name in clean or clean in n_name):
            return n['npc_id']
    return None

def parse_script_section(content):
    """
    단계_*.txt 내용 중 '9. 대본 관리' 섹션을 파싱하여 대본 항목 배열을 반환합니다.
    """
    # 대본 관리 위치 탐색 (\d+. 대본 관리)
    section_match = re.search(r'\d+\.\s*대본\s*관리.*?\n(.*)', content, re.DOTALL)
    if not section_match:
        return []

    section_text = section_match.group(1)

    # [1], [2], ... 단위로 분할
    raw_blocks = re.split(r'\n(?=\[\d+\])', section_text)
    script_lines = []

    for b in raw_blocks:
        b = b.strip()
        if not b.startswith('['):
            continue

        lines = b.split('\n')
        header_line = lines[0]

        # [1] 화자 타입: NPC
        type_match = re.search(r'화자\s*타입\s*:\s*([A-Za-z]+)', header_line)
        if not type_match:
            continue
        speaker_type = type_match.group(1).upper().strip()

        speaker = None
        speaker_label_html = None
        line_html = None
        audio_url = None
        owner_name = None

        for line in lines[1:]:
            line_str = line.strip()
            if line_str.startswith("화자:") or line_str.startswith("화자 :"):
                speaker = line_str.split(":", 1)[1].strip()
            elif line_str.startswith("화자 표시 HTML:") or line_str.startswith("화자 표시 HTML :"):
                speaker_label_html = line_str.split(":", 1)[1].strip()
            elif line_str.startswith("대사:") or line_str.startswith("대사 :"):
                line_html = line_str.split(":", 1)[1].strip()
            elif line_str.startswith("wav 파일:") or line_str.startswith("wav 파일 :") or line_str.startswith("audioUrl:") or line_str.startswith("audioUrl :"):
                val = line_str.split(":", 1)[1].strip()
                if val.startswith("http://") or val.startswith("https://"):
                    audio_url = val
            elif line_str.startswith("담당자:") or line_str.startswith("담당 플레이어:") or line_str.startswith("담당자 :") or line_str.startswith("담당 플레이어 :"):
                owner_name = line_str.split(":", 1)[1].strip()

        if line_html:
            script_lines.append({
                "speaker_type": speaker_type,
                "speaker": speaker,
                "speaker_label_html": speaker_label_html,
                "line_html": line_html,
                "audio_url": audio_url,
                "owner_name": owner_name,
            })

    return script_lines

def parse_step_file(file_path):
    """
    단계_*.txt 파일에서 StoryID, StepID 및 대본 관리 목록을 파싱합니다.
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

    story_id_match = re.search(r'StoryID\s*:\s*([a-fA-F0-9\-]+)', content)
    step_id_match = re.search(r'StepID\s*:\s*([a-fA-F0-9\-]+)', content)

    if not story_id_match or not step_id_match:
        print(f"[SKIP] StoryID 또는 StepID를 찾을 수 없음: {os.path.basename(file_path)}")
        return None

    story_id = story_id_match.group(1).strip()
    step_id = step_id_match.group(1).strip()
    raw_lines = parse_script_section(content)

    return {
        "file_name": os.path.basename(file_path),
        "story_id": story_id,
        "step_id": step_id,
        "raw_lines": raw_lines
    }

def update_script_db(target_path, dry_run=False):
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

    pool = SharedConnectionPool.get_instance()
    total_inserted = 0

    with pool.get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SET NAMES utf8mb4")

        for fpath in target_files:
            parsed = parse_step_file(fpath)
            if not parsed:
                continue

            story_id = parsed["story_id"]
            step_id = parsed["step_id"]
            raw_lines = parsed["raw_lines"]
            file_name = parsed["file_name"]

            if not raw_lines:
                print(f"[INFO] {file_name} -> 대본 관리 섹션에 입력된 대사 없음 (건너뜀)")
                continue

            roles, npcs = fetch_story_roles_and_npcs(cursor, story_id)
            if not roles:
                print(f"[WARNING] {file_name} -> 스토리({story_id})에 등록된 플레이어 역할(role)이 없습니다.")
                continue

            # 기존 DB에 저장된 audio_url 및 owner_role_id 맵핑 (line_order -> dict)
            cursor.execute("""
                SELECT line_order, audio_url, owner_role_id
                FROM story_step_script_line
                WHERE step_id = %s
            """, (step_id,))
            existing_db_map = {row['line_order']: row for row in cursor.fetchall()}

            # 비-플레이어(NPC/DIRECTIVE) 줄 담당 교대 index
            non_player_count = 1  # 1부터 시작하여 첫 번째 NPC대사가 2번째 역할(예: 마커스)부터 시작

            db_lines = []
            for order, l in enumerate(raw_lines):
                stype = l["speaker_type"]
                line_html = l["line_html"]
                speaker = l["speaker"]
                speaker_label_html = l["speaker_label_html"]
                audio_url = l["audio_url"]
                owner_name = l["owner_name"]

                # 기존 audio_url 보존: 텍스트 파일에서 새로운 http(s) audio_url이 제공되지 않은 경우 기존 DB 값 유지
                if not audio_url and order in existing_db_map and existing_db_map[order]['audio_url']:
                    audio_url = existing_db_map[order]['audio_url']

                role_id = None
                npc_id = None
                owner_role_id = None

                if stype == "PLAYER":
                    role_id = match_role(speaker or speaker_label_html or owner_name, roles)
                    if not role_id:
                        # 기본 첫 번째 역할로 fallback
                        role_id = roles[0]["role_id"]
                    owner_role_id = role_id
                elif stype == "NPC":
                    npc_id = match_npc(speaker or speaker_label_html, npcs)
                    if owner_name:
                        owner_role_id = match_role(owner_name, roles)
                    # 기존 owner_role_id 보존: 텍스트 파일에 담당자가 명시되지 않은 경우 기존 DB 값 유지
                    if not owner_role_id and order in existing_db_map and existing_db_map[order]['owner_role_id']:
                        owner_role_id = existing_db_map[order]['owner_role_id']
                    if not owner_role_id:
                        owner_role_id = roles[non_player_count % len(roles)]["role_id"]
                        non_player_count += 1
                else:  # DIRECTIVE
                    speaker_label_html = None
                    if owner_name:
                        owner_role_id = match_role(owner_name, roles)
                    # 기존 owner_role_id 보존: 텍스트 파일에 담당자가 명시되지 않은 경우 기존 DB 값 유지
                    if not owner_role_id and order in existing_db_map and existing_db_map[order]['owner_role_id']:
                        owner_role_id = existing_db_map[order]['owner_role_id']
                    if not owner_role_id:
                        owner_role_id = roles[non_player_count % len(roles)]["role_id"]
                        non_player_count += 1

                db_lines.append({
                    "step_id": step_id,
                    "line_order": order,
                    "speaker_type": stype,
                    "role_id": role_id,
                    "npc_id": npc_id,
                    "owner_role_id": owner_role_id,
                    "speaker_label_html": speaker_label_html,
                    "line_html": line_html,
                    "audio_url": audio_url
                })

            print(f"[PARSED] {file_name} (StepID: {step_id}) -> {len(db_lines)}개 대본 줄 파싱 완료")

            if dry_run:
                for idx, dl in enumerate(db_lines, 1):
                    role_name_str = next((r['character_name'] for r in roles if r['role_id'] == dl['role_id']), '-')
                    owner_name_str = next((r['character_name'] for r in roles if r['role_id'] == dl['owner_role_id']), '-')
                    audio_info = f" | Audio: {dl['audio_url']}" if dl['audio_url'] else ""
                    print(f"  [{idx}] Type: {dl['speaker_type']} | Role: {role_name_str} | Owner: {owner_name_str}{audio_info} | Text: {dl['line_html'][:30]}...")
                continue

            # DB 덮어쓰기 (기존 deletion -> batch insert)
            delete_sql = "DELETE FROM story_step_script_line WHERE step_id = %s"
            cursor.execute(delete_sql, (step_id,))

            insert_sql = """
                INSERT INTO story_step_script_line (
                    line_id, step_id, line_order, speaker_type, role_id, npc_id, owner_role_id, speaker_label_html, line_html, audio_url
                ) VALUES (UUID(), %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            insert_data = [
                (
                    dl["step_id"],
                    dl["line_order"],
                    dl["speaker_type"],
                    dl["role_id"],
                    dl["npc_id"],
                    dl["owner_role_id"],
                    dl["speaker_label_html"],
                    dl["line_html"],
                    dl["audio_url"],
                ) for dl in db_lines
            ]

            cursor.executemany(insert_sql, insert_data)
            total_inserted += len(insert_data)
            print(f"[SUCCESS] {file_name} -> DB에 {len(insert_data)}개 대본 줄 저장 완료")

        if not dry_run:
            conn.commit()

    print("-" * 70)
    if dry_run:
        print("[DRY-RUN] 검증 완료. DB 변경 없음.")
    else:
        print(f"[DONE] 총 {total_inserted}개 대본 줄이 DB(story_step_script_line)에 성공적으로 업데이트되었습니다.")

def main():
    parser = argparse.ArgumentParser(description="단계_*.txt 파일의 '9. 대본 관리' 대사 항목을 MySQL story_step_script_line DB 테이블에 업데이트합니다.")
    parser.add_argument("target_path", help="단계 텍스트 파일 또는 단계 파일들이 포함된 디렉토리 경로")
    parser.add_argument("--dry-run", action="store_true", help="실제 DB 업데이트 없이 파싱 결과만 확인")
    args = parser.parse_args()

    update_script_db(args.target_path, dry_run=args.dry_run)

if __name__ == "__main__":
    main()
