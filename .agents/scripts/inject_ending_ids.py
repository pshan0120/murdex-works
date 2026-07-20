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
    
    cursor.execute("SELECT ending_id, ending_name FROM story_ending WHERE story_id = %s", (story_id,))
    db_endings = {e['ending_name']: e['ending_id'] for e in cursor.fetchall()}

file_path = r"c:\dev\KLIEN\murdex\works\바스타즈 오브 더 유니버스\texts\엔딩_공통.txt"
with open(file_path, "r", encoding="utf-8") as f:
    text = f.read()

# Manual mapping for title differences
name_mapping = {
    '감춰진 얼굴': '찬탈당한 옥좌'
}

def inject_ending_id(match):
    original = match.group(0)
    title = match.group(2).strip() # group 2 is the actual title without '제목: '
    
    db_title = name_mapping.get(title, title)
    ending_id = db_endings.get(db_title)
    
    if ending_id:
        return f"{original}\nEndingID : {ending_id}"
    else:
        print(f"Warning: ID not found for '{title}' (searched as '{db_title}')")
        return original

# Check if EndingID is already present anywhere, to avoid double injection
if "EndingID :" in text:
    print("Removing existing EndingIDs before reinjection...")
    text = re.sub(r'\nEndingID\s*:\s*[a-fA-F0-9\-]+\n', '\n', text)

new_text = re.sub(r'(제목:\s*(.*))', inject_ending_id, text)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(new_text)

print(f"Injected Ending IDs into {file_path}")
