# -*- coding: utf-8 -*-
import re

fp = r'c:\dev\KLIEN\murdex\works\바스타즈 오브 더 유니버스\texts\엔딩_HTML.txt'
with open(fp, encoding='utf-8') as f:
    content = f.read()

pairs = [
    ('마신 다크 시리어스', 'mystery'),
    ('류크(스컬크러셔)', 'character-skullcrusher'),
    ('스컬크러셔', 'character-skullcrusher'),
    ('말리스', 'character-malice'),
    ('발로그', 'character-balrog'),
    ('발트라', 'character-valtra'),
    ('고어후프', 'character-gorehoof'),
    ('슬리더', 'character-slither'),
    ('엘드리치', 'character-eldritch'),
    ('다크 시리어스', 'mystery'),
]

total = 0
for name, cls in pairs:
    pattern = r'(<span class="script-character">)(' + re.escape(name) + r')(</span>)'
    repl = r'\1<span class="' + cls + r'">\2</span>\3'
    content, n = re.subn(pattern, repl, content)
    print(f'{name}: {n}건')
    total += n

with open(fp, 'w', encoding='utf-8') as f:
    f.write(content)
print(f'총 {total}건 교체 완료')
