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

def parse_group_file(group_file_path):
    """
    단서_그룹.txt에서 그룹명 -> group_id 매핑을 추출합니다.
    """
    mapping = {}
    if not os.path.exists(group_file_path):
        print(f"Warning: Group file not found at {group_file_path}")
        return mapping
        
    with open(group_file_path, "r", encoding="utf-8") as f:
        text = f.read()
        
    # Example format:
    # 5. 연회장
    # GroupID : 7c37aab4-1180-4f89-9ce3-1bd15dcfc4e6
    blocks = text.split("\n\n")
    for block in blocks:
        name_match = re.search(r'\d+\.\s+(.*?)\n', block)
        id_match = re.search(r'GroupID\s*:\s*([a-f0-9\-]+)', block, re.IGNORECASE)
        
        if name_match and id_match:
            # We map the pure name, e.g., '연회장'
            name = name_match.group(1).strip()
            group_id = id_match.group(1).strip()
            mapping[name] = group_id
            
    return mapping

def parse_clue_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    blocks = []
    current_block = None
    in_html_section = False
    html_lines = []
    pending_tag = None
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("[clue_") and stripped.endswith("]"):
            pending_tag = stripped[1:-1]
            continue

        if line.startswith("이름 :"):
            if current_block:
                if in_html_section:
                    current_block["html"] = "".join(html_lines).strip()
                blocks.append(current_block)
                
            current_block = {"name": line.replace("이름 :", "").strip()}
            if pending_tag:
                current_block["tag"] = pending_tag
                pending_tag = None
            in_html_section = False
            html_lines = []
            
        elif current_block:
            if line.startswith("variant_id :") or line.startswith("variantId :"):
                val = line.split(":", 1)[1].strip()
                current_block["variant_id"] = val
            elif line.startswith("clue_id :") or line.startswith("clueId :"):
                val = line.split(":", 1)[1].strip()
                current_block["clue_id"] = val
            elif line.startswith("정렬순서 :"):
                current_block["order"] = line.replace("정렬순서 :", "").strip()
            elif line.startswith("단서 그룹 :"):
                # e.g., "05_연회장" -> extract "연회장"
                group_val = line.replace("단서 그룹 :", "").strip()
                current_block["raw_group"] = group_val
            elif line.startswith("단서 그룹 ID :") or line.startswith("groupId :"):
                val = line.split(":", 1)[1].strip()
                current_block["group_id"] = val
            elif line.startswith("HTML :"):
                in_html_section = True
            elif in_html_section:
                # "이미지생성용 프롬프트" marks the end of HTML
                if line.startswith("이미지생성용 프롬프트") or line.startswith("이름 :") or line.startswith("단서 그룹 :") or line.startswith("단서 그룹 ID :") or line.startswith("groupId :") or line.startswith("파일명 :"):
                    in_html_section = False
                    current_block["html"] = "".join(html_lines).strip()
                    
                    if line.startswith("단서 그룹 :"):
                        group_val = line.replace("단서 그룹 :", "").strip()
                        current_block["raw_group"] = group_val
                    elif line.startswith("단서 그룹 ID :") or line.startswith("groupId :"):
                        val = line.split(":", 1)[1].strip()
                        current_block["group_id"] = val
                else:
                    html_lines.append(line)
            else:
                # Catch 단서 그룹 if it appears after HTML
                if line.startswith("단서 그룹 :"):
                    group_val = line.replace("단서 그룹 :", "").strip()
                    current_block["raw_group"] = group_val
                elif line.startswith("단서 그룹 ID :") or line.startswith("groupId :"):
                    val = line.split(":", 1)[1].strip()
                    current_block["group_id"] = val
                    
    # Add last block
    if current_block:
        if in_html_section:
            current_block["html"] = "".join(html_lines).strip()
        blocks.append(current_block)
        
    return blocks

def map_groups(blocks, group_mapping):
    for block in blocks:
        # If group_id is already parsed from "단서 그룹 ID :", use it
        if "group_id" in block:
            g_id = block["group_id"]
            if g_id == "없음" or g_id == "None" or not g_id:
                block["group_id"] = None
            continue

        raw_group = block.get("raw_group", "")
        if raw_group == "없음" or raw_group == "시작 지급" or not raw_group:
            block["group_id"] = None
        else:
            parts = raw_group.split("_", 1)
            if len(parts) > 1 and parts[0].isdigit():
                clean_name = parts[1].replace("_", " ")
            else:
                clean_name = raw_group.replace("_", " ")
                
            if clean_name == "서쪽 환기구":
                clean_name = "서쪽 환풍구"
            elif clean_name == "지하 배양실":
                clean_name = "지하 주 배양실"
                
            group_id = group_mapping.get(clean_name)
            if not group_id:
                group_id = group_mapping.get(raw_group)
                
            if not group_id:
                # Fuzzy match fallback
                for g_name, g_id in group_mapping.items():
                    if clean_name in g_name or g_name in clean_name:
                        group_id = g_id
                        break
                        
            block["group_id"] = group_id
            
def update_db(blocks, dry_run=False):
    if dry_run:
        print("\n[DRY RUN] The following database updates would be executed:\n")
        for idx, block in enumerate(blocks, 1):
            print(f"--- Block {idx} ---")
            print(f"Tag: {block.get('tag')}")
            print(f"Name (clue_name): {block.get('name')}")
            print(f"Clue ID: {block.get('clue_id')}")
            print(f"Variant ID: {block.get('variant_id')}")
            print(f"Order (clue_order): {block.get('order')}")
            print(f"Group ID: {block.get('group_id')} (Raw: {block.get('raw_group')})")
            html_snippet = block.get('html', '')[:80] + ('...' if len(block.get('html', '')) > 80 else '')
            print(f"HTML (snippet): {html_snippet}\n")
        return len(blocks), len(blocks)
        
    pool = SharedConnectionPool.get_instance()
    success_count = 0
    
    with pool.get_connection() as conn:
        cursor = conn.cursor()
        
        for block in blocks:
            v_id = block.get("variant_id")
            c_id = block.get("clue_id")
            html_content = block.get("html")
            c_name = block.get("name")
            c_order = block.get("order")
            g_id = block.get("group_id")
            
            if not v_id or not c_id:
                continue
                
            if html_content is None:
                continue
                
            try:
                # Update clue_variant
                cursor.execute(
                    "UPDATE clue_variant SET clue_content = %s, clue_name = %s WHERE variant_id = %s", 
                    (html_content, c_name, v_id)
                )
                affected1 = cursor.rowcount
                
                # Update clue
                cursor.execute(
                    "UPDATE clue SET clue_order = %s, group_id = %s WHERE clue_id = %s",
                    (c_order, g_id, c_id)
                )
                affected2 = cursor.rowcount
                
                if affected1 > 0 or affected2 > 0:
                    success_count += 1
                else:
                    print(f"Warning: No rows updated for variant {v_id} / clue {c_id} (check if UUIDs match DB)")
            except Exception as e:
                print(f"Failed to update variant {v_id}: {e}")
                
        conn.commit()
        
    return success_count, len(blocks)

def main():
    parser = argparse.ArgumentParser(description="Update clue DB from clue text file.")
    parser.add_argument("file_path", help="Path to the clue text file (e.g. 단서.txt)")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be updated without committing to DB")
    parser.add_argument("--exclude-clue-ids", nargs="*", default=[], help="Clue IDs to exclude from update")
    parser.add_argument("--target-clues", nargs="*", default=[], help="Target clue tags/IDs/numbers to update (e.g. clue_11 clue_13)")
    args = parser.parse_args()
    
    if not os.path.exists(args.file_path):
        print(f"Error: File not found: {args.file_path}")
        sys.exit(1)
        
    # group file is expected to be in the same directory
    group_file_path = os.path.join(os.path.dirname(args.file_path), "단서_그룹.txt")
    
    print(f"Parsing groups from {group_file_path} ...")
    group_mapping = parse_group_file(group_file_path)
    print(f"Loaded {len(group_mapping)} groups.")
        
    print(f"Parsing {args.file_path} ...")
    blocks = parse_clue_file(args.file_path)
    print(f"Found {len(blocks)} clue blocks.")
    
    # 변형 단서 제외 (사용자 요청에 따라 변형 단서는 수동 관리)
    blocks = [b for b in blocks if "(변형)" not in b.get("name", "")]
    
    # 제외 대상 clue_id 필터링
    if args.exclude_clue_ids:
        exclude_set = set(args.exclude_clue_ids)
        before_count = len(blocks)
        blocks = [b for b in blocks if b.get("clue_id") not in exclude_set]
        print(f"Excluded {before_count - len(blocks)} clues based on --exclude-clue-ids: {args.exclude_clue_ids}")

    # 타겟 단서 필터링
    if args.target_clues:
        targets = set()
        for item in args.target_clues:
            # Handle comma separated strings if passed as one arg
            for sub in item.replace(',', ' ').split():
                clean_item = sub.strip()
                if clean_item:
                    targets.add(clean_item)
                    targets.add(clean_item.lower())
                    if clean_item.isdigit():
                        targets.add(f"clue_{clean_item.zfill(2)}")
                        targets.add(f"clue_{int(clean_item)}")
                    elif clean_item.lower().startswith("clue_"):
                        num_part = clean_item.lower().replace("clue_", "")
                        if num_part.isdigit():
                            targets.add(num_part)
                            targets.add(str(int(num_part)))

        filtered_blocks = []
        for b in blocks:
            tag = (b.get("tag") or "").lower()
            c_id = (b.get("clue_id") or "").lower()
            v_id = (b.get("variant_id") or "").lower()
            c_name = (b.get("name") or "").lower()
            
            if (tag in targets or 
                c_id in targets or 
                v_id in targets or 
                any(t in tag for t in targets if len(t) > 2) or
                any(t in c_name for t in targets if len(t) > 2)):
                filtered_blocks.append(b)
        
        print(f"Filtered {len(filtered_blocks)} clues matching targets: {args.target_clues}")
        blocks = filtered_blocks

    map_groups(blocks, group_mapping)
    
    if args.dry_run:
        update_db(blocks, dry_run=True)
    else:
        print("Updating database...")
        success, total = update_db(blocks, dry_run=False)
        print(f"Done. Updated {success} / {total} clue blocks.")

if __name__ == "__main__":
    main()
