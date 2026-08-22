# -*- coding: utf-8 -*-
import re, json

ROLE_MAP_PATH = r"C:\dev\KLIEN\murdex\works\바스타즈 오브 더 유니버스\texts\_role_id_map.json"
with open(ROLE_MAP_PATH, encoding="utf-8") as f:
    roles = json.load(f)
name_to_role_id = {r["character_name"]: r["role_id"] for r in roles}

with open(r"C:\dev\KLIEN\murdex\works\바스타즈 오브 더 유니버스\texts\backup\db_state_원본(수정전).json", encoding="utf-8") as f:
    backup = json.load(f)

ending = next(e for e in backup["endings"] if e["ending_name"] == "감춰진 얼굴")
html = ending["ending_story"]

# Strip the reading-guide note entirely (redundant once display_type=SCRIPT)
html = re.sub(r'<div class="reading-guide">.*?</div>\s*', '', html, flags=re.S)
# Strip the trailing ending-result footer (redundant with ending_name header already shown)
html = re.sub(r'<div class="ending-result">.*?</div>\s*', '', html, flags=re.S)
# Unwrap details/summary — flatten into plain content so our block scanner can walk it linearly
html = html.replace('<details class="ending-details">', '').replace('</details>', '')
html = re.sub(r'<summary class="suspense-msg">(.*?)</summary>', r'<p class="suspense-msg">\1</p>', html, flags=re.S)

line_re = re.compile(
    r'<div class="script-line">\s*'
    r'<span class="script-character">(?P<label>.*?)</span>:\s*'
    r'(?P<content>.*?)\s*'
    r'</div>',
    re.S
)
name_in_label_re = re.compile(r'<span class="character-[\w-]+">([^<(]+)')

def resolve_role(label_html):
    """label_html may be a simple <span class="character-x">이름</span>
    or a compound custom label like <span class="mystery">다크 시리어스(엘드리치)</span>."""
    names_found = re.findall(r'<span class="character-(\w[\w-]*)">([^<]+)</span>', label_html)
    if names_found:
        # first matching known character name wins
        for slug, name in names_found:
            if name in name_to_role_id:
                return name_to_role_id[name], label_html
    # fallback: look for a bare character name mentioned anywhere in the label, incl. parens e.g. "(엘드리치)"
    for name, rid in name_to_role_id.items():
        if name in re.sub(r'<[^>]+>', '', label_html):
            return rid, label_html
    return None, label_html

lines = []
order = 0
pos = 0
# Walk the html top-to-bottom, alternating between script-line matches and the
# plain narration text that sits between them (both are DIRECTIVE unless matched below).
tokens = []  # list of ("dialogue", match) or ("text", str)
last_end = 0
for m in line_re.finditer(html):
    if m.start() > last_end:
        tokens.append(("text", html[last_end:m.start()]))
    tokens.append(("dialogue", m))
    last_end = m.end()
if last_end < len(html):
    tokens.append(("text", html[last_end:]))

def extract_paragraphs(chunk):
    """Pull out quote-box / p / script-direction block contents as separate narration beats."""
    beats = []
    for qm in re.finditer(r'<div class="quote-box">\s*(.*?)\s*</div>', chunk, re.S):
        beats.append(qm.group(1).strip())
    chunk_wo_quotebox = re.sub(r'<div class="quote-box">.*?</div>', '', chunk, flags=re.S)
    for pm in re.finditer(r'<p(?:\s+class="[^"]*")?>\s*(.*?)\s*</p>', chunk_wo_quotebox, re.S):
        beats.append(pm.group(1).strip())
    for dm in re.finditer(r'<div class="script-direction">\s*(.*?)\s*</div>', chunk_wo_quotebox, re.S):
        # avoid double-counting direction text that's already inside a <p> we captured (rare in this file)
        beats.append(dm.group(1).strip())
    return [b for b in beats if b]

# present roles in this ending, in first-appearance order, for local round-robin
present_roles = []
for kind, val in tokens:
    if kind == "dialogue":
        rid, _ = resolve_role(val.group("label"))
        if rid and rid not in present_roles:
            present_roles.append(rid)
rr_idx = 0
def next_owner():
    global rr_idx
    if not present_roles:
        return None
    rid = present_roles[rr_idx % len(present_roles)]
    rr_idx += 1
    return rid

for kind, val in tokens:
    if kind == "dialogue":
        role_id, label_html = resolve_role(val.group("label"))
        if not role_id:
            print("WARNING: unresolved speaker label:", val.group("label"))
            continue
        lines.append({
            "lineOrder": order, "speakerType": "PLAYER",
            "roleId": role_id, "npcId": None, "ownerRoleId": role_id,
            "speakerLabelHtml": label_html, "lineHtml": val.group("content").strip(),
            "audioUrl": None
        })
        order += 1
    else:
        for beat in extract_paragraphs(val):
            lines.append({
                "lineOrder": order, "speakerType": "DIRECTIVE",
                "roleId": None, "npcId": None, "ownerRoleId": next_owner(),
                "speakerLabelHtml": None, "lineHtml": beat,
                "audioUrl": None
            })
            order += 1

print(f"Parsed {len(lines)} lines. Present roles (in order): {len(present_roles)}")
OUT = r"C:\dev\KLIEN\murdex\works\바스타즈 오브 더 유니버스\texts\script_migration\ending1_감춰진얼굴_lines.json"
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(lines, f, ensure_ascii=False, indent=2)
