import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

murdex_api_path = r"c:\dev\KLIEN\murdex\murdex-api"
if murdex_api_path not in sys.path:
    sys.path.append(murdex_api_path)

from infrastructure.database.shared_connection_pool import SharedConnectionPool

pool = SharedConnectionPool.get_instance()

with pool.get_connection() as conn:
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT story_id, title FROM story WHERE title LIKE '%바스타즈%'")
    stories = cursor.fetchall()
    print("Stories found:", stories)
    
    if stories:
        story_id = stories[0]['story_id']
        cursor.execute("SELECT ending_id, ending_name FROM story_ending WHERE story_id = %s", (story_id,))
        endings = cursor.fetchall()
        for e in endings:
            print(f"{e['ending_name']} : {e['ending_id']}")
