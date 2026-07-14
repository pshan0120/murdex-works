import sys
import os
import re
import json

def inject_missing_clue_ids(file_path, clues_json_path):
    if not os.path.exists(file_path):
        print(f"File {file_path} not found!")
        return
        
    with open(clues_json_path, "r", encoding="utf-8") as f:
        clues = json.load(f)
        
    clue_map = {c["clue_name"]: c for c in clues}
    
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    out_lines = []
    injected_count = 0
    
    i = 0
    while i < len(lines):
        line = lines[i]
        out_lines.append(line)
        
        # Check for 이름 : xxx
        name_match = re.match(r'^이름\s*:\s*(.+)', line.strip())
        if name_match:
            clue_name = name_match.group(1).strip()
            
            # Check if already injected
            already_injected = False
            look_ahead = 1
            file_name = None
            
            while i + look_ahead < len(lines) and look_ahead <= 100:
                nxt_line = lines[i + look_ahead].strip()
                if "clue_id :" in nxt_line:
                    already_injected = True
                if nxt_line.startswith("파일명 :"):
                    file_name = nxt_line.replace("파일명 :", "").strip()
                    break
                look_ahead += 1
                
            if not already_injected and file_name:
                # Deduce original DB name from filename
                # e.g., 13_서재_3 -> 서재#3
                file_match = re.match(r'^\d+_(.+)_(.+)$', file_name)
                if file_match:
                    db_clue_name = f"{file_match.group(1)}#{file_match.group(2)}"
                    clue_data = clue_map.get(db_clue_name)
                    if clue_data:
                        out_lines.append(f"clue_id : {clue_data['clue_id']}\n")
                        if clue_data['variant_id']:
                            out_lines.append(f"variant_id : {clue_data['variant_id']}\n")
                        injected_count += 1
                        print(f"Injected for {clue_name} (mapped from {file_name} -> {db_clue_name})")
                    else:
                        print(f"Warning: Deduced DB clue '{db_clue_name}' not found for '{clue_name}'")
                else:
                    print(f"Warning: Filename format unknown for '{clue_name}': {file_name}")
                    
        i += 1
        
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(out_lines)
        
    print(f"Injected {injected_count} missing clue_ids into {file_path}.")

if __name__ == "__main__":
    inject_missing_clue_ids("단서.txt", "dump_bastards_clues.json")
