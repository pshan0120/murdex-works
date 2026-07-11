import os
import glob
import re

directory = "c:/dev/KLIEN/murdex/works/누룩꽃 필 무렵/texts"
files = glob.glob(os.path.join(directory, "*.txt")) + glob.glob(os.path.join(directory, "*.md"))

replacements = {
    "백서연 박사님": "백서연 작가님",
    "백서연 박사": "백서연 작가",
    "백 박사님": "백 작가님",
    "백 박사": "백 작가",
    "서연 박사님": "서연 작가님",
    "서연 박사": "서연 작가",
    "박사님": "작가님",
}

for filepath in files:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    new_content = content
    for old, new in replacements.items():
        new_content = new_content.replace(old, new)
        
    # Also catch standalone "박사가", "박사는", "박사를", "박사에게" etc if they refer to her
    new_content = re.sub(r'\b박사(가|는|를|에게|의|와|과|도|만)\b', r'작가\1', new_content)
    # Catch bare '박사 '
    new_content = re.sub(r'\b박사\s', '작가 ', new_content)

    if new_content != content:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Updated {os.path.basename(filepath)}")

print("Replacement complete.")