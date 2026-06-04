import os
import glob

path = r"c:\dev\KLIEN\murdex\works\바스타즈 오브 더 유니버스\texts"
files = glob.glob(os.path.join(path, "*.txt"))

for file in files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if "발트라" in content:
        content = content.replace("발트라", "엘란트라")
        with open(file, 'w', encoding='utf-8', newline='') as f:
            f.write(content)

valtra_file = os.path.join(path, "역할_발트라.txt")
elantra_file = os.path.join(path, "역할_엘란트라.txt")
if os.path.exists(valtra_file):
    os.rename(valtra_file, elantra_file)

valtra_backup_file = os.path.join(path, "역할_발트라_backup.txt")
elantra_backup_file = os.path.join(path, "역할_엘란트라_backup.txt")
if os.path.exists(valtra_backup_file):
    os.rename(valtra_backup_file, elantra_backup_file)

print("Python replace and rename complete.")
