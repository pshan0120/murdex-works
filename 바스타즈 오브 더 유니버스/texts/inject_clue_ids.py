import sys
import os
import re
import json

def inject_clue_ids(file_path, clues_json_path, story_id):
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
    story_id_injected = False
    
    i = 0
    while i < len(lines):
        line = lines[i]
        out_lines.append(line)
        
        # Inject StoryID at the top
        if not story_id_injected and line.startswith("#"):
            if i + 1 < len(lines) and "StoryID :" not in lines[i+1] and "StoryID :" not in lines[i+2]:
                out_lines.append(f"\nStoryID : {story_id}\n")
            story_id_injected = True
            
        # Check for 이름 : xxx
        name_match = re.match(r'^이름\s*:\s*(.+)', line.strip())
        if name_match:
            clue_name = name_match.group(1).strip()
            
            # Check if next lines already have clue_id
            already_injected = False
            look_ahead = 1
            while i + look_ahead < len(lines) and look_ahead <= 3:
                if "clue_id :" in lines[i + look_ahead]:
                    already_injected = True
                    break
                look_ahead += 1
                
            if not already_injected:
                clue_data = clue_map.get(clue_name)
                if not clue_data:
                    # Try substring match
                    for c_name, c_data in clue_map.items():
                        if c_name in clue_name or clue_name in c_name:
                            clue_data = c_data
                            break
                            
                if clue_data:
                    out_lines.append(f"clue_id : {clue_data['clue_id']}\n")
                    if clue_data['variant_id']:
                        out_lines.append(f"variant_id : {clue_data['variant_id']}\n")
                    injected_count += 1
                else:
                    print(f"Warning: Clue '{clue_name}' not found in DB!")
                    
        i += 1
        
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(out_lines)
        
    print(f"Injected {injected_count} clue_ids into {file_path}.")

if __name__ == "__main__":
    story_id = "a8d3c16b-3910-4fc6-82fa-aed0379904f9"
    inject_clue_ids("단서.txt", "dump_bastards_clues.json", story_id)
