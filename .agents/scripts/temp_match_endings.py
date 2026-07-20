import sys
import os
import re

sys.stdout.reconfigure(encoding='utf-8')

murdex_api_path = r"c:\dev\KLIEN\murdex\murdex-api"
if murdex_api_path not in sys.path:
    sys.path.append(murdex_api_path)

from infrastructure.database.shared_connection_pool import SharedConnectionPool

pool = SharedConnectionPool.get_instance()

with pool.get_connection() as conn:
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT story_id, title FROM story WHERE title LIKE '%바스타즈%'")
    story_id = cursor.fetchall()[0]['story_id']
    
    cursor.execute("SELECT ending_id, ending_name, ending_story FROM story_ending WHERE story_id = %s", (story_id,))
    db_endings = cursor.fetchall()
    
    for e in db_endings:
        if "마지막 촛불이 흔들리는 왕좌의 방" in e['ending_story']:
            print(f"Match found in DB! Name: {e['ending_name']}, ID: {e['ending_id']}")
