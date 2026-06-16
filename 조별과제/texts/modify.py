import sys
import re

file_path = r'c:\dev\KLIEN\murdex\works\조별과제\texts\단계정보_대본1.txt'
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines):
    # Process only lines 18-162 (index 17 to 161)
    if 17 <= i <= 161:
        # First, modify the script character spans
        line = line.replace('<span class=\"script-character\">이준서</span>', '<span class=\"script-character character-lee\">이준서</span>')
        line = line.replace('<span class=\"script-character\">한세린</span>', '<span class=\"script-character character-han\">한세린</span>')
        line = line.replace('<span class=\"script-character\">최도윤</span>', '<span class=\"script-character character-choi\">최도윤</span>')
        line = line.replace('<span class=\"script-character\">황기순</span>', '<span class=\"script-character character-hwang\">황기순</span>')
        
        # Now find names in the text outside of the tags and replace them
        # To avoid replacing names already inside tags, we can use regex
        # Negative lookbehind/ahead for tag characters
        
        def replace_name(text, name, cls):
            parts = re.split(r'(<[^>]+>)', text)
            for j in range(len(parts)):
                if not parts[j].startswith('<'):
                    parts[j] = re.sub(rf'(?<![가-힣]){name}(?![가-힣])', f'<span class=\"{cls}\">{name}</span>', parts[j])
            return ''.join(parts)
            
        line = replace_name(line, '이준서', 'character-lee')
        line = replace_name(line, '준서', 'character-lee')
        line = replace_name(line, '한세린', 'character-han')
        line = replace_name(line, '세린', 'character-han')
        line = replace_name(line, '최도윤', 'character-choi')
        line = replace_name(line, '도윤', 'character-choi')
        line = replace_name(line, '황기순', 'character-hwang')
        line = replace_name(line, '기순', 'character-hwang')
        
    new_lines.append(line)

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print('Done!')
