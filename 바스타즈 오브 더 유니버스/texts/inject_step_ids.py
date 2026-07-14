import os
import json
import glob
import re

story_id = "a8d3c16b-3910-4fc6-82fa-aed0379904f9"
json_file = "bastards_steps.json"

with open(json_file, "r", encoding="utf-8") as f:
    steps = json.load(f)

# Create mapping of step_order to step_id
step_map = {str(s["step_order"]): s["step_id"] for s in steps}

# Find all 단계_*.txt files
txt_files = glob.glob("단계_*.txt")

for file_path in txt_files:
    # Extract step order from filename (e.g. 단계_1_서막.txt -> 1)
    match = re.search(r'단계_(\d+)_', file_path)
    if not match:
        print(f"Skipping {file_path} - couldn't extract step order.")
        continue
        
    step_order = match.group(1)
    if step_order not in step_map:
        print(f"Skipping {file_path} - no matching step_id for order {step_order}.")
        continue
        
    step_id = step_map[step_order]
    
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    # Check if already prepended
    if len(lines) > 0 and "StoryID" in lines[0]:
        print(f"{file_path} already has StoryID. Skipping.")
        continue
        
    # Prepend lines
    prefix = f"StoryID : {story_id}\nStepID : {step_id}\n\n"
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(prefix)
        f.writelines(lines)
        
    print(f"Updated {file_path} with StoryID and StepID.")
