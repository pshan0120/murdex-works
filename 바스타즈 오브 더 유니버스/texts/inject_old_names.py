import sys
import os
import re
import json

def inject_old_names(file_path, clues_json_path):
    if not os.path.exists(file_path):
        print(f"File {file_path} not found!")
        return
        
    with open(clues_json_path, "r", encoding="utf-8") as f:
        clues = json.load(f)
        
    # Map clue_id -> db_clue_name
    clue_id_to_name = {c["clue_id"]: c["clue_name"] for c in clues}
    
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    out_lines = []
    injected_count = 0
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        name_match = re.match(r'^이름\s*:\s*(.+)', line.strip())
        if name_match:
            current_name = name_match.group(1).strip()
            
            # Find clue_id
            clue_id = None
            look_ahead = 1
            while i + look_ahead < len(lines) and look_ahead <= 50:
                nxt = lines[i + look_ahead].strip()
                if nxt.startswith("clue_id :"):
                    clue_id = nxt.replace("clue_id :", "").strip()
                    break
                look_ahead += 1
                
            out_lines.append(line)
            
            if clue_id:
                db_name = clue_id_to_name.get(clue_id)
                if db_name and db_name != current_name:
                    # Check if 예전 이름 is already there
                    if i + 1 < len(lines) and "예전 이름 :" in lines[i+1]:
                        pass # Already there
                    else:
                        out_lines.append(f"예전 이름 : {db_name}\n")
                        injected_count += 1
                        print(f"Added '예전 이름 : {db_name}' for '{current_name}'")
        else:
            out_lines.append(line)
            
        i += 1
        
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(out_lines)
        
    print(f"Injected {injected_count} old names into {file_path}.")

if __name__ == "__main__":
    inject_old_names("단서.txt", "dump_bastards_clues.json")
