import os
import glob

story_id = "11ac5811-9d96-4756-ad87-7d18764662ce"
step_mapping = {
    1: "f364e220-7d0f-4927-b8ae-e667a16cc62b",
    2: "4fabbaea-b0b9-467c-8b48-3d85a2dbce5e",
    3: "074b3044-7c90-4354-997e-a7bb6d4db011",
    4: "f5e6d372-d462-4843-a5d3-3e2da3795a7e",
    5: "eb315c53-b2ef-4fff-8768-92b4e8513038",
    6: "3889d6a2-684c-488e-801c-a032f2fefa6f",
    7: "e7dd36e8-79c5-4d47-a3da-c9bfa1a4622d",
    8: "a1d2579e-17fd-43ed-81ed-e83db561c4e1",
    9: "3aebe151-99ba-42d1-a1f5-a5d5d9b1cf4a"
}

folder_path = r"c:\dev\KLIEN\murdex\works\누룩꽃 필 무렵\texts"

for step_num, step_id in step_mapping.items():
    search_pattern = os.path.join(folder_path, f"단계_{step_num}_*.txt")
    files = glob.glob(search_pattern)
    for file_path in files:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        if "StoryID :" not in content:
            header = f"StoryID : {story_id}\nStepID : {step_id}\n\n"
            new_content = header + content
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"Updated: {os.path.basename(file_path)}")
