# -*- coding: utf-8 -*-
import re, json, sys
sys.path.append(r"C:\dev\KLIEN\murdex\works\바스타즈 오브 더 유니버스\texts\script_migration")
from script_utils import load_role_map, strip_wrapping_quotes

name_to_role_id, _ = load_role_map()

SRC = r"C:\dev\KLIEN\murdex\works\바스타즈 오브 더 유니버스\texts\backup\단계_2_대면_원본(수정전).txt"
with open(SRC, encoding="utf-8") as f:
    text = f.read()

# Extract the single script-container block
container_match = re.search(r'<div class="script-container">(.*?)<!-- 대본 영역 끝 -->', text, re.S)
container = container_match.group(1)

# Each script-line div (single-line in source, may include nested spans/quotes)
line_pattern = re.compile(
    r'<div class="script-line">\s*'
    r'<span class="script-character"><span class="character-(?P<slug>[\w-]+)">(?P<name>[^<]+)</span></span>:\s*'
    r'(?P<content>.*?)\s*'
    r'</div>',
    re.S
)

lines = []
order = 0
for m in line_pattern.finditer(container):
    name = m.group("name")
    role_id = name_to_role_id.get(name)
    if not role_id:
        print(f"WARNING: unmapped character name: {name}")
        continue
    content = strip_wrapping_quotes(m.group("content"))
    lines.append({
        "lineOrder": order,
        "speakerType": "PLAYER",
        "roleId": role_id,
        "npcId": None,
        "ownerRoleId": role_id,
        "speakerLabelHtml": f'<span class="character-{m.group("slug")}">{name}</span>',
        "lineHtml": content,
        "audioUrl": None
    })
    order += 1

print(f"Parsed {len(lines)} lines")
OUT = r"C:\dev\KLIEN\murdex\works\바스타즈 오브 더 유니버스\texts\script_migration\step2_대면_lines.json"
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(lines, f, ensure_ascii=False, indent=2)
