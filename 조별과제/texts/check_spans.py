
import sys
import re

# Set encoding to utf-8 for output
sys.stdout.reconfigure(encoding='utf-8')

with open(r'c:\dev\KLIEN\murdex\works\조별과제\texts\단서_전체_HTML.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()

characters = {
    '이준서': 'character-lee',
    '준서': 'character-lee',
    '한세린': 'character-han',
    '세린': 'character-han',
    '황기순': 'character-hwang',
    '기순': 'character-hwang',
    '최도윤': 'character-choi',
    '도윤': 'character-choi'
}

def is_decorated(line, name, cls):
    # This is a bit tricky. We want to find if 'name' exists but is NOT inside the span.
    # We can count total occurrences and compare with decorated occurrences.
    
    # Total occurrences of name
    total = line.count(name)
    if total == 0:
        return True
        
    # Occurrences that are already decorated
    # We look for <span class="cls">name</span>
    decorated = line.count(f'<span class="{cls}">{name}</span>')
    
    # If there are more total occurrences than decorated ones, it might be undecorated.
    # But wait, if name is '준서' and we have <span class="character-lee">이준서</span>,
    # then '준서' is counted in total but not in decorated (as '준서').
    # Let's subtract those.
    
    if name == '준서':
        total -= line.count('이준서')
    if name == '세린':
        total -= line.count('한세린')
    if name == '기순':
        total -= line.count('황기순')
    if name == '도윤':
        total -= line.count('최도윤')
        
    return total <= decorated

with open(r'c:\dev\KLIEN\murdex\works\조별과제\texts\undecorated_lines.txt', 'w', encoding='utf-8') as out:
    for i, line in enumerate(lines):
        line_num = i + 1
        # Only check HTML content lines
        if not (line.strip().startswith('<') or line.startswith('  ')):
            continue
        
        if line.strip() in ['<div class="story-content">', '</div>', '------------------------------------------------------------']:
            continue

        for name, cls in characters.items():
            if not is_decorated(line, name, cls):
                out.write(f"Line {line_num}: {line.strip()}\n")
                break
