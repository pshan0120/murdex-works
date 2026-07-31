import sys
import json

murdex_api_path = r"c:\dev\KLIEN\murdex\murdex-api"
if murdex_api_path not in sys.path:
    sys.path.append(murdex_api_path)

try:
    from infrastructure.database.shared_connection_pool import SharedConnectionPool
except ImportError:
    print("Error: Could not import SharedConnectionPool.")
    sys.exit(1)

def get_clues(story_id):
    pool = SharedConnectionPool.get_instance()
    with pool.get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT c.clue_id, v.variant_id, v.clue_name
            FROM clue c
            JOIN clue_variant v ON c.clue_id = v.clue_id
            WHERE c.story_id = %s
            ORDER BY v.clue_name
            """,
            (story_id,)
        )
        clues = cursor.fetchall()
    return clues

if __name__ == "__main__":
    story_id = "ad38faf1-eccc-43b5-b419-b8b00b2e4add"
    clues = get_clues(story_id)
    
    with open("dump_mokryun_clues.json", "w", encoding="utf-8") as f:
        json.dump(clues, f, ensure_ascii=False, indent=2)
    print("Dumped clues to dump_mokryun_clues.json")
