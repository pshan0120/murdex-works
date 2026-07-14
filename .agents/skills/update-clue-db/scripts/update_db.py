import sys
import os
import argparse

# Add murdex-api to path to use shared_connection_pool
murdex_api_path = r"c:\dev\KLIEN\murdex\murdex-api"
if murdex_api_path not in sys.path:
    sys.path.append(murdex_api_path)

try:
    from infrastructure.database.shared_connection_pool import SharedConnectionPool
except ImportError:
    print("Error: Could not import SharedConnectionPool. Ensure murdex-api path is correct and dependencies are installed.")
    sys.exit(1)

def parse_clue_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    blocks = []
    current_block = None
    in_html_section = False
    html_lines = []
    
    for i, line in enumerate(lines):
        if line.startswith("이름 :"):
            # Save previous block
            if current_block:
                if in_html_section:
                    current_block["html"] = "".join(html_lines).strip()
                blocks.append(current_block)
                
            current_block = {"name": line.replace("이름 :", "").strip()}
            in_html_section = False
            html_lines = []
            
        elif current_block:
            if line.startswith("variant_id :"):
                current_block["variant_id"] = line.replace("variant_id :", "").strip()
            elif line.startswith("clue_id :"):
                current_block["clue_id"] = line.replace("clue_id :", "").strip()
            elif line.startswith("HTML :"):
                in_html_section = True
            elif in_html_section:
                # Assuming "이미지생성용 프롬프트:" or similar demarcates end of HTML
                if line.startswith("이미지생성용 프롬프트:") or line.startswith("장소 :") or line.startswith("파일명 :"):
                    in_html_section = False
                    current_block["html"] = "".join(html_lines).strip()
                else:
                    html_lines.append(line)
                    
    # Add last block
    if current_block:
        if in_html_section:
            current_block["html"] = "".join(html_lines).strip()
        blocks.append(current_block)
        
    return blocks

def update_db(blocks):
    pool = SharedConnectionPool.get_instance()
    success_count = 0
    
    with pool.get_connection() as conn:
        cursor = conn.cursor()
        
        for block in blocks:
            v_id = block.get("variant_id")
            html_content = block.get("html")
            
            if not v_id:
                continue
                
            if html_content is None:
                continue
                
            try:
                # Update clue_content in clue_variant table
                cursor.execute(
                    "UPDATE clue_variant SET clue_content = %s WHERE variant_id = %s", 
                    (html_content, v_id)
                )
                if cursor.rowcount > 0:
                    success_count += 1
            except Exception as e:
                print(f"Failed to update variant {v_id}: {e}")
                
        conn.commit()
        
    return success_count, len(blocks)

def main():
    parser = argparse.ArgumentParser(description="Update clue_variant DB from clue text file.")
    parser.add_argument("file_path", help="Path to the clue text file (e.g. 단서.txt)")
    args = parser.parse_args()
    
    if not os.path.exists(args.file_path):
        print(f"Error: File not found: {args.file_path}")
        sys.exit(1)
        
    print(f"Parsing {args.file_path} ...")
    blocks = parse_clue_file(args.file_path)
    print(f"Found {len(blocks)} clue blocks.")
    
    print("Updating database...")
    success, total = update_db(blocks)
    print(f"Done. Updated {success} / {total} clue blocks.")

if __name__ == "__main__":
    main()
