import json
import re

prefix_map = {
    "스컬크러셔": 2,
    "엘드리치": 3,
    "말리스": 4,
    "발로그": 5,
    "고어후프": 6,
    "슬리더": 7,
    "엘란트라": 8
}

def inject_ending_ids(file_path, endings_json_path):
    with open(endings_json_path, "r", encoding="utf-8") as f:
        endings = json.load(f)
        
    ending_map = {(e["ending_name"], e["ending_order"]): e["ending_id"] for e in endings}
    
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    out_lines = []
    injected_count = 0
    
    i = 0
    while i < len(lines):
        line = lines[i]
        out_lines.append(line)
        
        # Check if we already have an EndingID to avoid double injection
        if "EndingID :" in line:
            # But wait, we are appending line first. It's fine for re-runs to not inject again.
            pass
            
        title_match = re.match(r'^제목:\s*(.+)', line.strip())
        if title_match:
            ending_name = title_match.group(1).strip()
            
            # Look ahead for "순서:"
            ending_order = None
            look_ahead = 1
            while i + look_ahead < len(lines) and look_ahead <= 10:
                order_line = lines[i + look_ahead].strip()
                if "EndingID :" in order_line:
                    # Already injected
                    break
                    
                order_match = re.match(r'^순서:\s*(.+)', order_line)
                if order_match:
                    order_val = order_match.group(1).strip()
                    if order_val.isdigit():
                        ending_order = int(order_val)
                    else:
                        # e.g. 스컬크러셔-1
                        parts = order_val.split("-")
                        if len(parts) == 2 and parts[0] in prefix_map and parts[1].isdigit():
                            ending_order = prefix_map[parts[0]] * 10 + int(parts[1])
                        else:
                            print(f"Warning: Unknown order format '{order_val}'")
                    break
                look_ahead += 1
                
            if ending_order is not None:
                # Check if it was already injected
                # By peeking ahead to see if the next line is EndingID
                if i + 1 < len(lines) and "EndingID :" in lines[i+1]:
                    pass # Already injected
                else:
                    ending_id = ending_map.get((ending_name, ending_order))
                    if ending_id:
                        out_lines.append(f"EndingID : {ending_id}\n")
                        injected_count += 1
                    else:
                        print(f"Warning: Ending '{ending_name}' with order {ending_order} not found in DB!")
            else:
                pass
                
        i += 1
        
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(out_lines)
        
    print(f"Injected {injected_count} EndingIDs into {file_path}.")

if __name__ == "__main__":
    # Common endings (orders are numeric)
    # 2026-08-21: 엔딩_공통.txt는 엔딩_메타.txt로 개명됨. 이 EndingID 주입은 이미 완료된 상태라
    # 재실행할 필요는 없지만, 혹시 다시 돌릴 경우를 대비해 파일명만 최신으로 맞춰둠.
    inject_ending_ids("엔딩_메타.txt", "story_endings.json")
    # Individual endings (orders are e.g. 스컬크러셔-1)
    inject_ending_ids("엔딩_개별.txt", "story_endings.json")
