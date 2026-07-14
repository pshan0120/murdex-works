import os
import glob

folder_path = r"c:\dev\KLIEN\murdex\works\누룩꽃 필 무렵\texts"

time_mapping = {
    "1": "무제한",
    "2": "10분",
    "3": "20분",
    "4": "20분",
    "5": "20분",
    "6": "40분",
    "7": "5분",
    "8": "무제한",
    "9": "무제한"
}

for step_num, time_val in time_mapping.items():
    search_pattern = os.path.join(folder_path, f"단계_{step_num}_*.txt")
    files = glob.glob(search_pattern)
    for file_path in files:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        # Find "4. 예상 소요 시간"
        for i, line in enumerate(lines):
            if "4. 예상 소요 시간" in line:
                # The next line is the time
                if i + 1 < len(lines):
                    lines[i+1] = f"{time_val}\n"
                break
                
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        print(f"Updated {os.path.basename(file_path)} to {time_val}")
