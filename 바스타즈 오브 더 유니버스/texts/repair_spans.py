import re

fp = r'c:\dev\KLIEN\murdex\works\바스타즈 오브 더 유니버스\texts\엔딩_HTML.txt'
with open(fp, encoding='utf-8') as f:
    text = f.read()

# 1. Clean up messed up placeholders and double spans
text = re.sub(r'__SPAN_.*?__(.*?)__', r'\1', text)
# Simple recovery: remove nested spans of the same class
text = re.sub(r'<span class="(.*?)"><span class="\1">(.*?)</span></span>', r'<span class="\1">\2</span>', text)
text = re.sub(r'<span class="(.*?)"><span class="\1">(.*?)</span></span>', r'<span class="\1">\2</span>', text) # Repeat for deep nesting

# 2. Comprehensive cleanup of role spans from Ending 2 onwards
marker = "<!-- Ending 2"
split_index = text.find(marker)
header = text[:split_index]
content = text[split_index:]

# Classes and roles
roles = {
    '말리스': 'character-malice',
    '스컬크러셔': 'character-skullcrusher',
    '발로그': 'character-balrog',
    '발트라': 'character-valtra',
    '고어후프': 'character-gorehoof',
    '슬리더': 'character-slither',
    '엘드리치': 'character-eldritch',
    '다크 시리어스': 'mystery',
    '마신 다크 시리어스': 'mystery',
    '골든 킹': 'character-goldenking',
    '마스터즈': 'character-masters',
    '바스타즈': 'highlight',
    '류크': 'character-skullcrusher',
    '류크(스컬크러셔)': 'character-skullcrusher'
}

# Remove ALL existing role spans to start fresh
# Match <span class="character-...">...</span> or mystery or highlight
content = re.sub(r'<span class="(character-|mystery|highlight).*?">(.*?)</span>', r'\2', content)
# Sometimes they might be nested in script-character. Clean those too.
content = re.sub(r'<span class="script-character">(.*?)</span>', r'<span class="script-character">\1</span>', content) # No-op just to be safe

# Now apply correctly
# Longest names first
sorted_names = sorted(roles.keys(), key=len, reverse=True)

# We use a state-machine or split approach
parts = re.split(r'(<span class="script-character">.*?</span>|<[^>]+>)', content)

for i in range(len(parts)):
    if i % 2 == 0: # Text node
        node = parts[i]
        for name in sorted_names:
            cls = roles[name]
            # Wrap name with a special temporary tag to avoid double matching
            node = re.sub(re.escape(name), f'__NEWSPAN_{cls}_{name}__', node)
        parts[i] = node
    else: # Tag or script-character span
        tag = parts[i]
        if 'class="script-character"' in tag:
            # Handle script character labels uniquely
            # Strip current content and wrap name
            inner = re.sub(r'<.*?>', '', tag) # Get plain name
            inner = inner.replace(':', '').strip()
            # If "마신 다크 시리어스", handle according to Ending 1 style (just "다크 시리어스" spanned?)
            # Actually, let's keep it simple: Nested span for the name.
            best_match = None
            for name in sorted_names:
                if name in inner:
                    best_match = name
                    break
            
            if best_match:
                cls = roles[best_match]
                # Special case for "마신 다크 시리어스" -> "<span class='mystery'>다크 시리어스</span>"
                if best_match == '마신 다크 시리어스':
                    parts[i] = f'<span class="script-character"><span class="mystery">다크 시리어스</span></span>'
                elif best_match == '다크 시리어스':
                    parts[i] = f'<span class="script-character"><span class="mystery">다크 시리어스</span></span>'
                else:
                    parts[i] = f'<span class="script-character"><span class="{cls}">{best_match}</span></span>'
            else:
                pass # Leave as is

final_content = "".join(parts)
for name in sorted_names:
    cls = roles[name]
    final_content = final_content.replace(f'__NEWSPAN_{cls}_{name}__', f'<span class="{cls}">{name}</span>')

with open(fp, 'w', encoding='utf-8') as f:
    f.write(header + final_content)

print("Done")
