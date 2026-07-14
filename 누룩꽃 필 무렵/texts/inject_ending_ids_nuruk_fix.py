import sys
import os
import re
import json

def inject_ending_ids(file_path, endings_json_path):
    if not os.path.exists(file_path):
        print(f"File {file_path} not found!")
        return
        
    with open(endings_json_path, "r", encoding="utf-8") as f:
        endings = json.load(f)
        
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    out_lines = []
    injected_count = 0
    
    i = 0
    while i < len(lines):
        line = lines[i]
        out_lines.append(line)
        
        # Check for both formats
        title_match_1 = re.match(r'^\[\[엔딩명:\s*(.+)\]\]', line.strip())
        title_match_2 = re.match(r'^제목:\s*(.+)', line.strip())
        
        title_match = title_match_1 or title_match_2
        if title_match:
            ending_name = title_match.group(1).strip()
            
            # Check if next lines already have EndingID
            look_ahead = 1
            already_injected = False
            while i + look_ahead < len(lines) and look_ahead <= 10:
                if "EndingID :" in lines[i + look_ahead]:
                    already_injected = True
                    break
                look_ahead += 1
                
            if not already_injected:
                # Substring match without checking order
                ending_id = None
                for e in endings:
                    db_name = e["ending_name"]
                    if db_name in ending_name or ending_name in db_name:
                        ending_id = e["ending_id"]
                        break
                        
                if ending_id:
                    out_lines.append(f"EndingID : {ending_id}\n")
                    injected_count += 1
                else:
                    print(f"Warning: Ending '{ending_name}' not found in DB!")
                    
        i += 1
        
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(out_lines)
        
    print(f"Injected {injected_count} EndingIDs into {file_path}.")

if __name__ == "__main__":
    inject_ending_ids("엔딩_공통.txt", "dump_nuruk_endings.json")
    inject_ending_ids("엔딩_개별.txt", "dump_nuruk_endings.json")
