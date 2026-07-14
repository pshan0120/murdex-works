import json
import re

with open("clue_groups.json", "r", encoding="utf-8") as f:
    groups = json.load(f)

group_map = {g["group_name"]: g["group_id"] for g in groups}

with open("단서_그룹.txt", "r", encoding="utf-8") as f:
    lines = f.readlines()

out_lines = []
injected_count = 0

for line in lines:
    out_lines.append(line)
    
    match = re.match(r'^\d+\.\s*(.+)', line.strip())
    if match:
        name = match.group(1).strip()
        if name in group_map:
            # Check if next line is already GroupID to avoid duplicate injection
            # But we are iterating, so we can't easily peek without index, 
            # let's just assume it's clean since it's the first run.
            out_lines.append(f"GroupID : {group_map[name]}\n")
            injected_count += 1
        else:
            print(f"Warning: '{name}' not found in DB")
            
with open("단서_그룹.txt", "w", encoding="utf-8") as f:
    f.writelines(out_lines)
    
print(f"Injected GroupID into {injected_count} groups.")
