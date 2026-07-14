import re
import json

with open(r'c:\dev\KLIEN\murdex\works\누룩꽃 필 무렵\texts\단서.txt', 'r', encoding='utf-8') as f:
    content = f.read()

clues = re.split(r'### \[clue_', content)[1:]
results = []
for c in clues:
    name_m = re.search(r'이름 : (.*?)\n', c)
    type_m = re.search(r'유형 : (.*?)\n', c)
    step_m = re.search(r'단계 : (.*?)\n', c)
    char_m = re.search(r'관련 : (.*?)\n', c)
    
    if not all([name_m, type_m, step_m, char_m]): continue
    
    c_type = type_m.group(1).strip()
    if c_type not in ['관찰', '통찰']: continue
    
    name = name_m.group(1).strip()
    step = step_m.group(1).strip()
    char = char_m.group(1).strip()
    
    # Try to get <li> contents from HTML
    li_matches = re.findall(r'<li>(.*?)</li>', c, re.DOTALL)
    if li_matches:
        text = " ".join([re.sub(r'<[^>]+>', '', li).strip() for li in li_matches])
    else:
        content_m = re.search(r'내용 :\n(.*?)(?=\nHTML :)', c, re.DOTALL)
        text = content_m.group(1).strip() if content_m else ''
    
    text = text.replace('\n', ' ')
    results.append({'char': char, 'step': step, 'type': c_type, 'text': text})

steps = {}
for r in results:
    s = r['step']
    if s not in steps: steps[s] = []
    steps[s].append(r)

out = []
for s in sorted(steps.keys()):
    out.append(f'==== {s} ====')
    for r in steps[s]:
        out.append(f"[{r['char']}] {r['type']}: {r['text']}")

with open(r'c:\dev\KLIEN\murdex\works\누룩꽃 필 무렵\texts\parsed_clues2.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
