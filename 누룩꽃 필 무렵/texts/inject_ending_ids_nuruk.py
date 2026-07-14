import sys
import os
import re

murdex_api_path = r"c:\dev\KLIEN\murdex\murdex-api"
if murdex_api_path not in sys.path:
    sys.path.append(murdex_api_path)

try:
    from infrastructure.database.shared_connection_pool import SharedConnectionPool
except ImportError:
    print("Error: Could not import SharedConnectionPool.")
    sys.exit(1)

def get_endings(story_id):
    pool = SharedConnectionPool.get_instance()
    with pool.get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT ending_id, ending_name, ending_order FROM story_ending WHERE story_id = %s",
            (story_id,)
        )
        endings = cursor.fetchall()
    return endings

def inject_ending_ids(file_path, endings):
    if not os.path.exists(file_path):
        print(f"File {file_path} not found!")
        return
        
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    out_lines = []
    injected_count = 0
    
    i = 0
    while i < len(lines):
        line = lines[i]
        out_lines.append(line)
        
        # Check for both formats
        title_match_1 = re.match(r'^\[\[엔딩명:\s*(.+)\]\]', line.strip())
        title_match_2 = re.match(r'^제목:\s*(.+)', line.strip())
        
        title_match = title_match_1 or title_match_2
        if title_match:
            ending_name = title_match.group(1).strip()
            
            # Look ahead for "순서:"
            ending_order = None
            look_ahead = 1
            while i + look_ahead < len(lines) and look_ahead <= 10:
                order_line = lines[i + look_ahead].strip()
                if "EndingID :" in order_line:
                    break
                    
                order_match = re.match(r'^순서:\s*(\d+)', order_line)
                if order_match:
                    ending_order = int(order_match.group(1))
                    break
                look_ahead += 1
                
            if ending_order is not None:
                if i + 1 < len(lines) and "EndingID :" in lines[i+1]:
                    pass # Already injected
                else:
                    # Substring match
                    ending_id = None
                    for e in endings:
                        db_name = e["ending_name"]
                        if e["ending_order"] == ending_order and (db_name in ending_name or ending_name in db_name):
                            ending_id = e["ending_id"]
                            break
                            
                    if ending_id:
                        out_lines.append(f"EndingID : {ending_id}\n")
                        injected_count += 1
                    else:
                        print(f"Warning: Ending '{ending_name}' with order {ending_order} not found in DB!")
            else:
                pass
                
        i += 1
        
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(out_lines)
        
    print(f"Injected {injected_count} EndingIDs into {file_path}.")

def main():
    story_id = "11ac5811-9d96-4756-ad87-7d18764662ce"
    endings = get_endings(story_id)
    
    inject_ending_ids("엔딩_공통.txt", endings)
    inject_ending_ids("엔딩_개별.txt", endings)

if __name__ == "__main__":
    main()
