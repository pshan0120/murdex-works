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

def get_group_ids(story_id):
    pool = SharedConnectionPool.get_instance()
    with pool.get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT group_id, group_name FROM clue_group WHERE story_id = %s",
            (story_id,)
        )
        groups = cursor.fetchall()
    return groups

def main():
    story_id = "fd09b053-3bce-4c0b-ac06-0287d42b86c3"
    groups = get_group_ids(story_id)
    
    group_map = {g["group_name"]: g["group_id"] for g in groups}
    print(f"Found {len(group_map)} groups in DB:")
    for name, gid in group_map.items():
        print(f" - {name}: {gid}")
        
    file_path = "단서_그룹.txt"
    if not os.path.exists(file_path):
        print(f"File {file_path} not found!")
        sys.exit(1)
        
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    out_lines = []
    injected_count = 0

    for line in lines:
        out_lines.append(line)
        
        match = re.match(r'^\d+\.\s*(.+)', line.strip())
        if match:
            name = match.group(1).strip()
            if name in group_map:
                out_lines.append(f"GroupID : {group_map[name]}\n")
                injected_count += 1
            else:
                print(f"Warning: '{name}' not found in DB")
                
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(out_lines)
        
    print(f"Injected GroupID into {injected_count} groups in {file_path}.")

if __name__ == "__main__":
    main()
