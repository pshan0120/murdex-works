
import os
filepath = r"c:\dev\KLIEN\murdex\works\누룩꽃 필 무렵\docx_extracted.txt"
with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

targets = ["632", "753", "871", "998", "1108", "1219"]
# these are the start of round 2. Let's capture from there to end of round 4.
for idx in [632, 753, 871, 998, 1108, 1219]:
    print(f"--- Line {idx} ---")
    for j in range(idx, min(idx+60, len(lines))):
        if "5라운드" in lines[j]:
            break
        print(lines[j].strip())
