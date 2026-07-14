import sys
import json

# Add murdex-api to path to use shared_connection_pool
murdex_api_path = r"c:\dev\KLIEN\murdex\murdex-api"
if murdex_api_path not in sys.path:
    sys.path.append(murdex_api_path)

try:
    from infrastructure.database.shared_connection_pool import SharedConnectionPool
except ImportError:
    print("Error: Could not import SharedConnectionPool.")
    sys.exit(1)

def get_step_ids(story_id):
    pool = SharedConnectionPool.get_instance()
    
    with pool.get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        # Fetch step_id and step_order
        cursor.execute(
            "SELECT step_id, step_order FROM story_step WHERE story_id = %s ORDER BY step_order",
            (story_id,)
        )
        steps = cursor.fetchall()
        
    return steps

if __name__ == "__main__":
    story_id = "a8d3c16b-3910-4fc6-82fa-aed0379904f9"
    steps = get_step_ids(story_id)
    print("Found steps:")
    for s in steps:
        print(f"Order: {s['step_order']}, StepID: {s['step_id']}")
    
    with open("bastards_steps.json", "w", encoding="utf-8") as f:
        json.dump(steps, f, ensure_ascii=False, indent=2)
