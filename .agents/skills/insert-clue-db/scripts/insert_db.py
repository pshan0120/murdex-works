import sys
import os
import re
import argparse
import uuid
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

murdex_api_path = r"c:\dev\KLIEN\murdex\murdex-api"
if murdex_api_path not in sys.path:
    sys.path.append(murdex_api_path)

try:
    from infrastructure.database.shared_connection_pool import SharedConnectionPool
except ImportError:
    print("Error: Could not import SharedConnectionPool. Ensure murdex-api path is correct.")
    sys.exit(1)

def parse_group_file(group_file_path):
    mapping = {}
    if not os.path.exists(group_file_path):
        return mapping
        
    with open(group_file_path, "r", encoding="utf-8") as f:
        text = f.read()
        
    blocks = text.split("\n\n")
    for block in blocks:
        name_match = re.search(r'\d+\.\s+(.*?)\n', block)
        id_match = re.search(r'GroupID\s*:\s*([a-f0-9\-]+)', block, re.IGNORECASE)
        
        if name_match and id_match:
            name = name_match.group(1).strip()
            group_id = id_match.group(1).strip()
            mapping[name] = group_id
            
    return mapping

def generate_ids_and_update_file(file_path):
    """
    파일을 읽어서 각 단서의 clue_id, variant_id가 없으면 생성하고,
    생성된 ID를 텍스트 파일에 바로 덮어씁니다.
    반환값은 갱신된 파일의 파싱된 블록 리스트와 story_id입니다.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    story_id = None
    updated_lines = []
    blocks = []
    
    current_block = None
    in_html_section = False
    html_lines = []
    
    for i, line in enumerate(lines):
        if line.startswith("StoryID :"):
            story_id = line.replace("StoryID :", "").strip()
            updated_lines.append(line)
            continue
            
        if line.startswith("이름 :"):
            if current_block:
                if in_html_section:
                    current_block["html"] = "".join(html_lines).strip()
                blocks.append(current_block)
                
            current_block = {
                "name": line.replace("이름 :", "").strip(),
                "clue_id": None,
                "variant_id": None
            }
            in_html_section = False
            html_lines = []
            updated_lines.append(line)
            
        elif current_block:
            if line.startswith("clue_id :"):
                val = line.replace("clue_id :", "").strip()
                if not val:
                    val = str(uuid.uuid4())
                    updated_lines.append(f"clue_id : {val}\n")
                else:
                    updated_lines.append(line)
                current_block["clue_id"] = val
                
            elif line.startswith("variant_id :"):
                val = line.replace("variant_id :", "").strip()
                if not val:
                    val = str(uuid.uuid4())
                    updated_lines.append(f"variant_id : {val}\n")
                else:
                    updated_lines.append(line)
                current_block["variant_id"] = val
                
            elif line.startswith("유형 :"):
                current_block["type"] = line.replace("유형 :", "").strip()
                updated_lines.append(line)
            elif line.startswith("소모AP :"):
                current_block["ap_cost"] = line.replace("소모AP :", "").strip()
                updated_lines.append(line)
            elif line.startswith("정렬순서 :"):
                current_block["order"] = line.replace("정렬순서 :", "").strip()
                updated_lines.append(line)
            elif line.startswith("중요도 :"):
                current_block["importance"] = line.replace("중요도 :", "").strip()
                updated_lines.append(line)
            elif line.startswith("교환 가능 여부 :"):
                current_block["is_exchangeable"] = line.replace("교환 가능 여부 :", "").strip()
                updated_lines.append(line)
            elif line.startswith("획득 가능 여부 :"):
                current_block["is_acquirable"] = line.replace("획득 가능 여부 :", "").strip()
                updated_lines.append(line)
            elif line.startswith("단서 그룹 :"):
                current_block["raw_group"] = line.replace("단서 그룹 :", "").strip()
                updated_lines.append(line)
            elif line.startswith("파일명 :"):
                current_block["filename"] = line.replace("파일명 :", "").strip()
                updated_lines.append(line)
            elif line.startswith("HTML :"):
                in_html_section = True
                updated_lines.append(line)
            elif in_html_section:
                if line.startswith("이미지생성용 프롬프트") or line.startswith("이름 :") or line.startswith("단서 그룹 :") or line.startswith("파일명 :"):
                    in_html_section = False
                    current_block["html"] = "".join(html_lines).strip()
                    updated_lines.append(line)
                    
                    if line.startswith("단서 그룹 :"):
                        current_block["raw_group"] = line.replace("단서 그룹 :", "").strip()
                    elif line.startswith("파일명 :"):
                        current_block["filename"] = line.replace("파일명 :", "").strip()
                else:
                    html_lines.append(line)
                    updated_lines.append(line)
            else:
                updated_lines.append(line)
        else:
            updated_lines.append(line)
            
    if current_block:
        if in_html_section:
            current_block["html"] = "".join(html_lines).strip()
        blocks.append(current_block)
        
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(updated_lines)
        
    return blocks, story_id

def map_fields(block, group_mapping):
    # Group mapping
    raw_group = block.get("raw_group", "")
    if raw_group == "없음" or raw_group == "":
        block["group_id"] = None
    else:
        if "_" in raw_group:
            clean_name = raw_group.split("_", 1)[1].replace("_", " ")
        else:
            clean_name = raw_group
            
        group_id = group_mapping.get(clean_name)
        if not group_id:
            group_id = group_mapping.get(raw_group)
        block["group_id"] = group_id
        
    # Enum / Boolean mappings
    typ_str = block.get("type", "")
    if "진술" in typ_str:
        block["clue_type"] = "TESTIMONY"
    elif "정보" in typ_str:
        block["clue_type"] = "INFORMATION"
    else:
        block["clue_type"] = "PHYSICAL"
        
    imp_str = block.get("importance", "")
    if "높음" in imp_str:
        block["importance_level"] = "HIGH"
    elif "낮음" in imp_str:
        block["importance_level"] = "LOW"
    else:
        block["importance_level"] = "MEDIUM"
        
    block["is_exchangeable"] = 1 if block.get("is_exchangeable") == "Y" else 0
    block["is_acquirable"] = 1 if block.get("is_acquirable") == "Y" else 0
    
    # Int mappings
    try:
        block["ap_cost"] = int(block.get("ap_cost", 0))
    except ValueError:
        block["ap_cost"] = 0
        
    try:
        block["clue_order"] = int(block.get("order", 0))
    except ValueError:
        block["clue_order"] = 0

def insert_db(blocks, story_id, dry_run=False):
    if dry_run:
        print(f"\n[DRY RUN] Would insert {len(blocks)} clues for story {story_id}.\n")
        return len(blocks), len(blocks)
        
    pool = SharedConnectionPool.get_instance()
    success_count = 0
    now = datetime.now()
    
    with pool.get_connection() as conn:
        cursor = conn.cursor()
        
        for block in blocks:
            c_id = block.get("clue_id")
            v_id = block.get("variant_id")
            if not c_id or not v_id:
                continue
                
            try:
                # 1. Insert into clue
                cursor.execute("""
                    INSERT INTO clue (
                        clue_id, story_id, clue_type, importance_level,
                        is_revealable, is_exchangeable, ap_cost, clue_order,
                        is_acquirable, group_id, is_disposable_read, is_hidden_possession,
                        created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    c_id, story_id, block["clue_type"], block["importance_level"],
                    0, block["is_exchangeable"], block["ap_cost"], block["clue_order"],
                    block["is_acquirable"], block["group_id"], 0, 0,
                    now, now
                ))
                
                # 2. Insert into clue_variant
                cursor.execute("""
                    INSERT INTO clue_variant (
                        variant_id, clue_id, clue_name, variant_type,
                        clue_content, clue_image_url, is_default, priority,
                        passcodes, passcode_ap_cost, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    v_id, c_id, block["name"], "DEFAULT",
                    block.get("html", ""), None, 1, 0,
                    None, 0, now, now
                ))
                
                success_count += 1
            except Exception as e:
                print(f"Failed to insert clue {block['name']} ({c_id}): {e}")
                
        conn.commit()
        
    return success_count, len(blocks)

def main():
    parser = argparse.ArgumentParser(description="Insert clues to DB and update text file.")
    parser.add_argument("file_path", help="Path to the clue text file (e.g. 단서.txt)")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be inserted without committing to DB")
    args = parser.parse_args()
    
    if not os.path.exists(args.file_path):
        print(f"Error: File not found: {args.file_path}")
        sys.exit(1)
        
    group_file_path = os.path.join(os.path.dirname(args.file_path), "단서_그룹.txt")
    group_mapping = parse_group_file(group_file_path)
    print(f"Loaded {len(group_mapping)} groups.")
        
    print(f"Parsing and updating IDs in {args.file_path} ...")
    blocks, story_id = generate_ids_and_update_file(args.file_path)
    
    if not story_id:
        print("Error: StoryID not found at the top of the file.")
        sys.exit(1)
        
    # 변형 단서 제외
    blocks = [b for b in blocks if "(변형)" not in b.get("name", "")]
    print(f"Found {len(blocks)} clue blocks to insert.")
    
    for b in blocks:
        map_fields(b, group_mapping)
    
    if args.dry_run:
        insert_db(blocks, story_id, dry_run=True)
    else:
        print("Inserting into database...")
        success, total = insert_db(blocks, story_id, dry_run=False)
        print(f"Done. Inserted {success} / {total} clue blocks.")

if __name__ == "__main__":
    main()
