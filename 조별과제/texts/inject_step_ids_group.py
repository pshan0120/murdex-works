import os
import sys
import glob

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
            "SELECT step_id, step_name FROM story_step WHERE story_id = %s",
            (story_id,)
        )
        steps = cursor.fetchall()
        
    return {s["step_name"]: s["step_id"] for s in steps}

def main():
    story_id = "fd09b053-3bce-4c0b-ac06-0287d42b86c3"
    step_map = get_step_ids(story_id)
    
    print(f"Found steps for story {story_id}:")
    for name, step_id in step_map.items():
        print(f"Name: {name}, StepID: {step_id}")
        
    txt_files = glob.glob("단계_*.txt")
    
    for file_path in txt_files:
        # Extract step name from filename (e.g. 단계_개강.txt -> 개강)
        base_name = os.path.basename(file_path)
        step_name = base_name.replace("단계_", "").replace(".txt", "")
        
        # Sometime names in DB might have slight variations, we'll try exact match first
        matched_id = step_map.get(step_name)
        
        if not matched_id:
            # Try matching by checking if step_name is a substring of DB name or vice-versa
            for db_name, db_id in step_map.items():
                if step_name in db_name or db_name in step_name:
                    matched_id = db_id
                    break
                    
        if not matched_id:
            print(f"Skipping {file_path} - no matching step_id for name '{step_name}'.")
            continue
            
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        # Check if already prepended
        if len(lines) > 0 and "StoryID" in lines[0]:
            print(f"{file_path} already has StoryID. Skipping.")
            continue
            
        # Prepend lines
        prefix = f"StoryID : {story_id}\nStepID : {matched_id}\n\n"
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(prefix)
            f.writelines(lines)
            
        print(f"Updated {file_path} with StoryID and StepID.")

if __name__ == "__main__":
    main()
