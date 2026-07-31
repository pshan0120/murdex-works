import os
import sys
import glob
import re

# Add murdex-api to path to use shared_connection_pool
murdex_api_path = r"c:\dev\KLIEN\murdex\murdex-api"
if murdex_api_path not in sys.path:
    sys.path.append(murdex_api_path)

try:
    from infrastructure.database.shared_connection_pool import SharedConnectionPool
except ImportError:
    print("Error: Could not import SharedConnectionPool.")
    sys.exit(1)

def get_step_ids(story_id):
    pool = SharedConnectionPool.get_instance()
    
    with pool.get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT step_id, step_order FROM story_step WHERE story_id = %s ORDER BY step_order",
            (story_id,)
        )
        steps = cursor.fetchall()
        
    return {str(s["step_order"]): s["step_id"] for s in steps}

def main():
    story_id = "ad38faf1-eccc-43b5-b419-b8b00b2e4add"
    step_map = get_step_ids(story_id)
    
    print(f"Found steps for story {story_id}:")
    for order, step_id in step_map.items():
        print(f"Order: {order}, StepID: {step_id}")
        
    txt_files = glob.glob("단계_*.txt")
    
    for file_path in txt_files:
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

if __name__ == "__main__":
    main()
