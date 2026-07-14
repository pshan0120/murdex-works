import json
import re

clue_txt_path = r"c:\dev\KLIEN\murdex\works\누룩꽃 필 무렵\texts\단서.txt"
mapping_file = r"c:\dev\KLIEN\murdex\murdex-api\clue_mapping.json"

with open(mapping_file, "r", encoding="utf-8") as f:
    mapping = json.load(f)

with open(clue_txt_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

blocks = []
start_idx = -1
name = None
step = None
char = None

step_name_to_order = {
    "준비": 1,
    "소개": 2,
    "조사": 3,
    "발견": 4,
    "시험": 5,
    "마지막": 6,
    "폭로": 7,
    "사건의 전말": 8,
    "에필로그": 9
}

def parse_step(line_val):
    # Try finding integer first
    match = re.search(r'\d+', line_val)
    if match:
        return int(match.group())
    
    # Otherwise check keywords
    for keyword, order in step_name_to_order.items():
        if keyword in line_val:
            return order
    return None

for i, line in enumerate(lines):
    if line.startswith("이름 :"):
        if start_idx != -1:
            blocks.append((start_idx, i-1, name, step, char))
        start_idx = i
        name = line.replace("이름 :", "").strip()
        step = None
        char = None
    elif line.startswith("단계 :") and start_idx != -1:
        step = parse_step(line)
    elif line.startswith("관련 :") and start_idx != -1:
        char = line.replace("관련 :", "").strip()
    elif line.startswith("위치 :") and start_idx != -1 and not char:
        char = line.replace("위치 :", "").strip()

if start_idx != -1:
    blocks.append((start_idx, len(lines)-1, name, step, char))

success = 0
for block in reversed(blocks):
    start_idx, end_idx, name, step, char = block
    
    db_name = name
    db_name = db_name.replace("당신의 비밀", "당신이 아는 것")
    db_name = db_name.replace("공용 타임라인", "공개 타임라인")
    
    # Try multiple keys
    keys_to_try = [
        f"{db_name}_{char}_{step}",
        f"{db_name}_None_{step}",
        f"{db_name}_None_None",
        f"{db_name}_{char}_None"
    ]
    
    match_key = None
    for k in keys_to_try:
        if k in mapping:
            match_key = k
            break
            
    if match_key:
        c_id = mapping[match_key]["clue_id"]
        v_id = mapping[match_key]["variant_id"]
        
        if start_idx + 1 < len(lines) and lines[start_idx+1].startswith("clue_id :"):
            pass
        else:
            lines.insert(start_idx+1, f"variant_id : {v_id}\n")
            lines.insert(start_idx+1, f"clue_id : {c_id}\n")
        success += 1
    else:
        print(f"Warning: Could not resolve '{name}', char='{char}', step='{step}'")

with open(clue_txt_path, "w", encoding="utf-8") as f:
    f.writelines(lines)

print(f"Migration completed. Injected {success} / {len(blocks)} blocks.")
