import sys
import os
import json

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

if __name__ == "__main__":
    story_id = "a8d3c16b-3910-4fc6-82fa-aed0379904f9"
    groups = get_group_ids(story_id)
    
    with open("clue_groups.json", "w", encoding="utf-8") as f:
        json.dump(groups, f, ensure_ascii=False, indent=2)
    print("Dumped to clue_groups.json")
