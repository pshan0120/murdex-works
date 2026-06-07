import sys, re
sys.stdout.reconfigure(encoding='utf-8')

roles = [
    (1, '백서연', 'Dr. Alberta'),
    (2, '류현수', 'Enrique'),
    (3, '박단희', 'Katherine'),
    (4, '정해준', 'Charles'),
    (5, '최도훈', 'Ernie'),
    (6, '강은지', 'Shirley')
]

original_file = r'c:\dev\KLIEN\murdex\works\누룩꽃 필 무렵\texts\원본.txt'
with open(original_file, 'r', encoding='utf-8') as f:
    original_text = f.read()

def extract_original_confession(eng_name):
    # Try finding Stage 6 Confessions for each character
    pattern = rf"(?s){eng_name} Confession.*?(?=\n\n\n|\n[A-Z][a-z]+ Confession|The end of the confession)"
    match = re.search(pattern, original_text, re.IGNORECASE)
    if match:
        return match.group(0).strip()
    return 'NOT FOUND'

output = '# Confession Comparison\n\n'

for r_num, kor_name, eng_name in roles:
    role_file = rf'c:\dev\KLIEN\murdex\works\누룩꽃 필 무렵\texts\역할_{r_num}_{kor_name}.txt'
    try:
        with open(role_file, 'r', encoding='utf-8') as f:
            role_text = f.read()
    except Exception as e:
        output += f"Error reading {role_file}: {e}\n"
        continue
    
    # Extract Korean confession
    kor_confession = ''
    match = re.search(r'(?s)<p class="confession-speech">\s*\"?(.*?)\"?\s*</p>', role_text)
    if match:
        kor_confession = match.group(1).strip()
    else:
        kor_confession = 'NOT FOUND'
        
    eng_confession = extract_original_confession(eng_name)
    
    output += f'## {r_num}. {kor_name} ({eng_name})\n\n'
    output += f'### Original\n{eng_confession}\n\n'
    output += f'### Translated\n{kor_confession}\n\n'
    output += '---\n\n'

with open(r'c:\dev\KLIEN\murdex\works\누룩꽃 필 무렵\texts\confession_comparison.md', 'w', encoding='utf-8') as f:
    f.write(output)
print('Done!')
