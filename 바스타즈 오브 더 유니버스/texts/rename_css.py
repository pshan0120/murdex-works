import os
import glob

# 1. Update text files
texts_path = r"c:\dev\KLIEN\murdex\works\바스타즈 오브 더 유니버스\texts"
text_files = glob.glob(os.path.join(texts_path, "*.txt"))

for file in text_files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if "character-valtra" in content:
        content = content.replace("character-valtra", "character-elantra")
        with open(file, 'w', encoding='utf-8', newline='') as f:
            f.write(content)

# 2. Update CSS file
css_file = r"c:\dev\KLIEN\murdex\works\바스타즈 오브 더 유니버스\styles\바스타즈_오브_더_유니버스.css"
if os.path.exists(css_file):
    with open(css_file, 'r', encoding='utf-8') as f:
        css_content = f.read()
        
    css_changed = False
    if "character-valtra" in css_content:
        css_content = css_content.replace("character-valtra", "character-elantra")
        css_changed = True
    if "발트라" in css_content:
        css_content = css_content.replace("발트라", "엘란트라")
        css_changed = True
        
    if css_changed:
        with open(css_file, 'w', encoding='utf-8', newline='') as f:
            f.write(css_content)

print("CSS class and file update complete.")
