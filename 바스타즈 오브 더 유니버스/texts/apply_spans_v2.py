import re

fp = r'c:\dev\KLIEN\murdex\works\바스타즈 오브 더 유니버스\texts\엔딩_HTML.txt'
with open(fp, encoding='utf-8') as f:
    text = f.read()

# Marker for Ending 2
marker = "<!-- Ending 2"
split_index = text.find(marker)
if split_index == -1:
    print("Marker not found")
    exit(1)

header = text[:split_index]
content = text[split_index:]

mappings = {
    '마신 다크 시리어스': ('mystery', '다크 시리어스'), # For script headers
    '다크 시리어스': ('mystery', '다크 시리어스'),
    '류크(스컬크러셔)': ('character-skullcrusher', '류크(스컬크러셔)'),
    '말리스': ('character-malice', '말리스'),
    '스컬크러셔': ('character-skullcrusher', '스컬크러셔'),
    '발로그': ('character-balrog', '발로그'),
    '발트라': ('character-valtra', '발트라'),
    '고어후프': ('character-gorehoof', '고어후프'),
    '슬리더': ('character-slither', '슬리더'),
    '엘드리치': ('character-eldritch', '엘드리치'),
    '골든 킹': ('character-goldenking', '골든 킹'),
    '마스터즈': ('character-masters', '마스터즈'),
    '바스타즈': ('highlight', '바스타즈'),
    '류크': ('character-skullcrusher', '류크'),
}

# 1. First, fix script headers to match user style: <span class="script-character"><span class="CLASS">NAME</span></span>
# Note: For "마신 다크 시리어스", the user in Ending 1 made it just "다크 시리어스" inside the nested span.
def fix_script_headers(text):
    for raw_name, (cls, name_to_use) in mappings.items():
        pattern = r'<span class="script-character">' + re.escape(raw_name) + r'</span>'
        replacement = f'<span class="script-character"><span class="{cls}">{name_to_use}</span></span>'
        text = re.sub(pattern, replacement, text)
    return text

# 2. Wrap plain text occurrences
# We must avoid replacing text that is already inside a <span> or is part of a tag.
# A safe way is to find all names and check if they are already wrapped.
def wrap_plain_text(text):
    # Sort names by length descending to match longest first
    sorted_names = sorted(mappings.keys(), key=len, reverse=True)
    
    for name in sorted_names:
        if name in ['마신 다크 시리어스', '류크(스컬크러셔)']: continue # Skip these for plain text as they are handled by their parts
        
        cls, _ = mappings[name]
        
        # Regex to find name NOT inside <...> and NOT already preceded by class="..." or >
        # More robust: use a callback with re.sub that checks context
        
        pattern = re.escape(name)
        
        def replace_func(match):
            m_text = match.group(0)
            start = match.start()
            
            # Simple check: is there a '<' before '>', or are we inside a span of the same role?
            # Check 15 chars before for existing span
            before = text[max(0, start-40):start]
            if f'class="{cls}"' in before or f'class=\'{cls}\'' in before:
                # Likely already spanned
                if '>' in before.split('<')[-1]:
                    return m_text
                return m_text # Already has the class nearby
            
            # Check if inside any tag
            if '<' in before and '>' not in before[before.rfind('<'):]:
                return m_text
                
            return f'<span class="{cls}">{m_text}</span>'

        # This is slightly dangerous if run multiple times. Let's use a more precise regex.
        # Match name if not preceded by character-class=" or > and not followed by </span>
        # But Korean text is complex.
        
        # Let's use a simpler marker: replace all existing spans with placeholders, replace, then restore.
        return text # Placeholder for now, I'll use a better logic below

def robust_wrap(text):
    # This function will find all text nodes and apply replacements only there.
    parts = re.split(r'(<[^>]+>)', text)
    sorted_names = sorted(mappings.keys(), key=len, reverse=True)
    
    for i in range(len(parts)):
        if i % 2 == 0: # This is a text node
            for name in sorted_names:
                cls, _ = mappings[name]
                # Avoid re-wrapping if the parent part was a script-character span (we already handled that)
                # Actually, parts[i] is just the text.
                
                # We should replace the name with span, but we must be careful not to match partials 
                # or already replaced parts.
                # Use a unique placeholder to avoid recursive replacement.
                parts[i] = re.sub(re.escape(name), f'__SPAN_{cls}_{name}__', parts[i])
    
    res = "".join(parts)
    # Final pass to restore placeholders
    for name in sorted_names:
        cls, _ = mappings[name]
        res = res.replace(f'__SPAN_{cls}_{name}__', f'<span class="{cls}">{name}</span>')
    return res

temp_content = fix_script_headers(content)
# We already have many spans in the content. robust_wrap will handle them because they are in parts[i] (odd indices).
final_content = robust_wrap(temp_content)

with open(fp, 'w', encoding='utf-8') as f:
    f.write(header + final_content)

print("Done")
