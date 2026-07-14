import sys
import os
import re
import json

def fix_clue_ids(file_path, clues_json_path):
    if not os.path.exists(file_path):
        print(f"File {file_path} not found!")
        return
        
    with open(clues_json_path, "r", encoding="utf-8") as f:
        clues = json.load(f)
        
    clue_map = {c["clue_name"]: c for c in clues}
    
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # We will process block by block. A block starts with [clue_...
    blocks = re.split(r'(?=\[clue_\d+\])', content)
    
    out_blocks = []
    
    for block in blocks:
        if not block.startswith('[clue_'):
            out_blocks.append(block)
            continue
            
        lines = block.split('\n')
        
        # Parse fields
        current_name = None
        file_name = None
        for line in lines:
            if line.startswith('이름 :'):
                current_name = line.replace('이름 :', '').strip()
            if line.startswith('파일명 :'):
                file_name = line.replace('파일명 :', '').strip()
                
        if not current_name or not file_name:
            out_blocks.append(block)
            continue
            
        # Deduce old_db_name
        old_db_name = None
        m = re.match(r'^\d+_(.+?)(?:_(.+))?$', file_name)
        if m:
            if m.group(2):
                old_db_name = f"{m.group(1)}#{m.group(2)}"
            else:
                old_db_name = m.group(1)
                
        if not old_db_name:
            print(f"Warning: Could not parse filename '{file_name}' for clue '{current_name}'")
            out_blocks.append(block)
            continue
            
        clue_data = clue_map.get(old_db_name)
        if not clue_data:
            # Fallback to current_name if old_db_name not in DB
            clue_data = clue_map.get(current_name)
            
        if not clue_data:
            print(f"Warning: Clue data not found for '{old_db_name}' or '{current_name}'")
            out_blocks.append(block)
            continue
            
        # Reconstruct block lines
        new_lines = []
        skip = False
        injected = False
        for line in lines:
            if line.startswith('이름 :') or line.startswith('예전 이름 :') or line.startswith('clue_id :') or line.startswith('variant_id :'):
                continue
                
            if line.startswith('유형 :') and not injected:
                # Inject here
                new_lines.append(f"이름 : {current_name}")
                if old_db_name != current_name:
                    new_lines.append(f"예전 이름 : {old_db_name}")
                new_lines.append(f"clue_id : {clue_data['clue_id']}")
                if clue_data['variant_id']:
                    new_lines.append(f"variant_id : {clue_data['variant_id']}")
                injected = True
                new_lines.append(line)
            else:
                new_lines.append(line)
                
        out_blocks.append('\n'.join(new_lines))
        
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(''.join(out_blocks))
        
    print(f"Fixed clues based on filename in {file_path}")

if __name__ == "__main__":
    fix_clue_ids("단서.txt", "dump_bastards_clues.json")
