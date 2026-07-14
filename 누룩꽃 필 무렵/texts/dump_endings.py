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

if __name__ == "__main__":
    story_id = "11ac5811-9d96-4756-ad87-7d18764662ce"
    endings = get_endings(story_id)
    
    with open("dump_nuruk_endings.json", "w", encoding="utf-8") as f:
        json.dump(endings, f, ensure_ascii=False, indent=2)
    print("Dumped endings to dump_nuruk_endings.json")
