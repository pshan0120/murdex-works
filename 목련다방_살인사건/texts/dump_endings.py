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
    story_id = "ad38faf1-eccc-43b5-b419-b8b00b2e4add"
    endings = get_endings(story_id)
    print("Endings:")
    for e in endings:
        print(f"Name: {e['ending_name']}, Order: {e['ending_order']}")
