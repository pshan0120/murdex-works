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
    if not speaker_str or not npcs:
        return None
    clean = speaker_str.strip()
    for n in npcs:
        n_name = (n['name'] or '').strip()
        if n_name and (n_name in clean or clean in n_name):
            return n['npc_id']
    return None


def ensure_npc(cursor, story_id, name, npcs, dry_run=False):
    """npc_character에 해당 이름의 NPC가 없으면 새로 생성하고 npcs 캐시에 추가한다.
    dry_run일 때는 실제 INSERT 없이 미리보기용 가짜 id만 반환한다(부작용 없음)."""
    npc_id = match_npc(name, npcs)
    if npc_id:
        return npc_id, npcs

    if dry_run:
        print(f"  [DRY-RUN] NPC '{name}'가 없어 생성이 필요합니다 (실제로는 생성하지 않음)")
        fake_row = {"npc_id": "(신규 생성 예정)", "name": name}
        return fake_row["npc_id"], npcs + [fake_row]

    cursor.execute("""
        SELECT COALESCE(MAX(npc_order), 0) + 1 AS next_order FROM npc_character WHERE story_id = %s
    """, (story_id,))
    next_order = cursor.fetchone()['next_order']

    cursor.execute("""
        INSERT INTO npc_character (npc_id, story_id, name, npc_order)
        VALUES (UUID(), %s, %s, %s)
    """, (story_id, name, next_order))

    cursor.execute("""
        SELECT npc_id, name FROM npc_character WHERE story_id = %s AND name = %s
    """, (story_id, name))
    row = cursor.fetchone()
    npcs = npcs + [row]
    print(f"  [NPC 생성] '{name}' (npc_id: {row['npc_id']})")
    return row['npc_id'], npcs


def parse_script_block(section_text):
    """'대본' 섹션 텍스트에서 [1], [2], ... 대사 항목 배열을 파싱한다."""
    raw_blocks = re.split(r'\n(?=\[\d+\])', section_text)
    script_lines = []

    for b in raw_blocks:
        b = b.strip()
        if not b.startswith('['):
            continue

        lines = b.split('\n')
        header_line = lines[0]

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


def parse_ending_script_file(file_path):
    """엔딩_대본.txt 파일을 EndingID 단위 블록으로 나누어 각 블록의 '대본' 섹션을 파싱한다."""
    if not os.path.exists(file_path):
        print(f"[ERROR] 파일을 찾을 수 없습니다: {file_path}")
        return []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(file_path, "r", encoding="utf-8-sig") as f:
            content = f.read()

    # EndingID 위치를 기준으로 파일을 블록 단위로 분할
    matches = list(re.finditer(r'EndingID\s*:\s*([a-fA-F0-9\-]+)', content))
    if not matches:
        print(f"[SKIP] EndingID를 찾을 수 없음: {os.path.basename(file_path)}")
        return []

    title_pattern = re.compile(r'제목\s*:\s*(.+)')

    results = []
    for idx, m in enumerate(matches):
        ending_id = m.group(1).strip()
        block_start = m.start()
        block_end = matches[idx + 1].start() if idx + 1 < len(matches) else len(content)
        block_text = content[block_start:block_end]

        # 블록 시작 바로 앞부분(제목 줄)은 이전 블록에 속하므로, 현재 블록 텍스트 앞쪽에서 제목을 못 찾을 수 있다.
        # 제목은 EndingID 바로 위에 있으므로 원본 content에서 별도로 탐색.
        preceding_text = content[:block_start]
        title_matches = title_pattern.findall(preceding_text)
        title = title_matches[-1].strip() if title_matches else "(제목 미상)"

        script_section_match = re.search(r'\n대본\s*\n(.*)', block_text, re.DOTALL)
        raw_lines = parse_script_block(script_section_match.group(1)) if script_section_match else []

        results.append({
            "ending_id": ending_id,
            "title": title,
            "raw_lines": raw_lines,
        })

    return results


def update_ending_script_db(target_path, dry_run=False, set_display_type=True):
    if not os.path.isfile(target_path):
        print(f"[ERROR] 대상 파일을 찾을 수 없습니다: {target_path}")
        return

    parsed_endings = parse_ending_script_file(target_path)
    if not parsed_endings:
        return

    pool = SharedConnectionPool.get_instance()
    total_inserted = 0
    total_endings_updated = 0

    with pool.get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SET NAMES utf8mb4")

        for parsed in parsed_endings:
            ending_id = parsed["ending_id"]
            title = parsed["title"]
            raw_lines = parsed["raw_lines"]

            if not raw_lines:
                print(f"[INFO] {title} ({ending_id}) -> 대본 섹션에 대사 없음 (건너뜀)")
                continue

            cursor.execute("SELECT story_id, ending_name FROM story_ending WHERE ending_id = %s", (ending_id,))
            ending_row = cursor.fetchone()
            if not ending_row:
                print(f"[WARNING] {title} ({ending_id}) -> DB에 존재하지 않는 엔딩입니다. 건너뜀.")
                continue

            story_id = ending_row["story_id"]

            roles, npcs = fetch_story_roles_and_npcs(cursor, story_id)
            if not roles:
                print(f"[WARNING] {title} -> 스토리({story_id})에 등록된 플레이어 역할(role)이 없습니다.")
                continue

            db_lines = []
            for order, l in enumerate(raw_lines):
                stype = l["speaker_type"]
                line_html = l["line_html"]
                speaker = l["speaker"]
                speaker_label_html = l["speaker_label_html"]
                audio_url = l["audio_url"]
                owner_name = l["owner_name"]

                role_id = None
                npc_id = None
                owner_role_id = None

                if stype == "PLAYER":
                    role_id = match_role(speaker or speaker_label_html or owner_name, roles)
                    if not role_id:
                        role_id = roles[0]["role_id"]
                    owner_role_id = role_id
                elif stype == "NPC":
                    npc_name = speaker or speaker_label_html
                    npc_id, npcs = ensure_npc(cursor, story_id, npc_name, npcs, dry_run=dry_run) if npc_name else (None, npcs)
                    if owner_name:
                        owner_role_id = match_role(owner_name, roles)
                    if not owner_role_id:
                        owner_role_id = roles[0]["role_id"]
                else:  # DIRECTIVE
                    speaker_label_html = None
                    if owner_name:
                        owner_role_id = match_role(owner_name, roles)
                    if not owner_role_id:
                        owner_role_id = roles[0]["role_id"]

                db_lines.append({
                    "ending_id": ending_id,
                    "line_order": order,
                    "speaker_type": stype,
                    "role_id": role_id,
                    "npc_id": npc_id,
                    "owner_role_id": owner_role_id,
                    "speaker_label_html": speaker_label_html,
                    "line_html": line_html,
                    "audio_url": audio_url
                })

            print(f"[PARSED] {title} (EndingID: {ending_id}) -> {len(db_lines)}개 대본 줄 파싱 완료")

            if dry_run:
                for idx, dl in enumerate(db_lines, 1):
                    speaker_str = dl["speaker_type"]
                    if dl["role_id"]:
                        speaker_str += ":" + next((r['character_name'] for r in roles if r['role_id'] == dl['role_id']), '-')
                    elif dl["npc_id"]:
                        speaker_str += ":" + next((n['name'] for n in npcs if n['npc_id'] == dl['npc_id']), '-')
                    owner_name_str = next((r['character_name'] for r in roles if r['role_id'] == dl['owner_role_id']), '-')
                    print(f"  [{idx}] {speaker_str} | Owner: {owner_name_str} | Text: {dl['line_html'][:30]}...")
                total_endings_updated += 1
                total_inserted += len(db_lines)
                continue

            delete_sql = "DELETE FROM story_ending_script_line WHERE ending_id = %s"
            cursor.execute(delete_sql, (ending_id,))

            insert_sql = """
                INSERT INTO story_ending_script_line (
                    line_id, ending_id, line_order, speaker_type, role_id, npc_id, owner_role_id, speaker_label_html, line_html, audio_url
                ) VALUES (UUID(), %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            insert_data = [
                (
                    dl["ending_id"], dl["line_order"], dl["speaker_type"], dl["role_id"],
                    dl["npc_id"], dl["owner_role_id"], dl["speaker_label_html"], dl["line_html"], dl["audio_url"],
                ) for dl in db_lines
            ]
            cursor.executemany(insert_sql, insert_data)

            if set_display_type:
                cursor.execute(
                    "UPDATE story_ending SET display_type = 'SCRIPT' WHERE ending_id = %s",
                    (ending_id,)
                )

            total_inserted += len(insert_data)
            total_endings_updated += 1
            print(f"[SUCCESS] {title} -> DB에 {len(insert_data)}개 대본 줄 저장 완료" + (" (display_type=SCRIPT)" if set_display_type else ""))

        if not dry_run:
            conn.commit()

    print("-" * 70)
    if dry_run:
        print(f"[DRY-RUN] 검증 완료. 엔딩 {total_endings_updated}개, 대사 {total_inserted}줄 파싱됨. DB 변경 없음.")
    else:
        print(f"[DONE] 엔딩 {total_endings_updated}개에 총 {total_inserted}개 대본 줄을 story_ending_script_line에 저장했습니다.")


def main():
    parser = argparse.ArgumentParser(description="엔딩_대본.txt의 각 엔딩별 대본을 MySQL story_ending_script_line에 저장하고 해당 엔딩의 display_type을 SCRIPT로 전환합니다.")
    parser.add_argument("target_path", help="엔딩_대본.txt 파일 경로")
    parser.add_argument("--dry-run", action="store_true", help="실제 DB 업데이트 없이 파싱 결과만 확인")
    parser.add_argument("--no-display-type", action="store_true", help="display_type을 SCRIPT로 바꾸지 않고 대본 줄만 저장")
    args = parser.parse_args()

    update_ending_script_db(args.target_path, dry_run=args.dry_run, set_display_type=not args.no_display_type)


if __name__ == "__main__":
    main()
