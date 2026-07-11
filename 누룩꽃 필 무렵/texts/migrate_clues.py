import os
import re

dir_path = "c:/dev/KLIEN/murdex/works/누룩꽃 필 무렵/texts"

characters = [
    {"file": "역할_1_백서연.txt", "eng": "seoyeon", "kor": "백서연"},
    {"file": "역할_2_류현수.txt", "eng": "hyunsu", "kor": "류현수"},
    {"file": "역할_3_박단희.txt", "eng": "danhee", "kor": "박단희"},
    {"file": "역할_4_정해준.txt", "eng": "haejun", "kor": "정해준"},
    {"file": "역할_5_최도훈.txt", "eng": "dohun", "kor": "최도훈"},
    {"file": "역할_6_강은지.txt", "eng": "eunji", "kor": "강은지"},
]

# Read clues
clues_path = os.path.join(dir_path, "단서.txt")
with open(clues_path, 'r', encoding='utf-8') as f:
    clues_content = f.read()

# Pattern for extraction
def extract_and_remove(content, title):
    # Regex to find <details> block with specific summary
    pattern = r'<details>\s*<summary>\s*' + title + r'\s*<span class="toggle-wrapper">.*?</span>\s*</summary>\s*<div class="collapsible-content">\s*(.*?)\s*</div>\s*</details>'
    match = re.search(pattern, content, flags=re.DOTALL)
    if match:
        extracted = match.group(1).strip()
        new_content = content[:match.start()] + content[match.end():]
        return extracted, new_content
    return None, content

for char in characters:
    role_path = os.path.join(dir_path, char['file'])
    with open(role_path, 'r', encoding='utf-8') as f:
        role_content = f.read()
    
    who_content, role_content = extract_and_remove(role_content, "당신은 누구인가")
    dark_content, role_content = extract_and_remove(role_content, "당신의 어두운 면")
    
    if who_content is None or dark_content is None:
        print(f"Failed to extract for {char['kor']}")
        continue
        
    # Write back role file
    with open(role_path, 'w', encoding='utf-8') as f:
        f.write(role_content)
        
    print(f"Extracted and updated {char['file']}")
    
    # Find timeline clue to insert before
    timeline_tag = f"### [clue_p_{char['eng']}_01]"
    tag_pos = clues_content.find(timeline_tag)
    if tag_pos == -1:
        print(f"Could not find timeline clue for {char['kor']}")
        continue
        
    # Extract order
    order_match = re.search(r'정렬순서 : (\d+)', clues_content[tag_pos:tag_pos+500])
    if order_match:
        timeline_order = int(order_match.group(1))
    else:
        timeline_order = 101 # default fallback
        
    who_order = timeline_order - 2
    dark_order = timeline_order - 1
    
    new_clues = f"""### [clue_p_{char['eng']}_00_who]

이름 : 당신은 누구인가
유형 : 통찰
단계 : 소개 단계
소모AP : 0
정렬순서 : {who_order}
중요도 : 높음
핵심 단서 여부 : N
교환 가능 여부 : N
획득 가능 여부 : N
획득 조건 존재 여부 : N
획득 조건 내용 : 없음
시작 표시 상태 : 뒷면
단계 시작시 자동 획득 : Y
관련 : {char['kor']}
의도 : 캐릭터 배경 및 정체성 인지
내용 :
{char['kor']}의 소개 단계 배경 정보
HTML :
<div class="story-content">
  <div class="document-page type-knowledge">
    <div class="section-title">당신은 누구인가</div>
    <div class="intro-narrative">
{who_content}
    </div>
  </div>
</div>

### [clue_p_{char['eng']}_00_dark]

이름 : 당신의 어두운 면
유형 : 통찰
단계 : 소개 단계
소모AP : 0
정렬순서 : {dark_order}
중요도 : 높음
핵심 단서 여부 : N
교환 가능 여부 : N
획득 가능 여부 : N
획득 조건 존재 여부 : N
획득 조건 내용 : 없음
시작 표시 상태 : 뒷면
단계 시작시 자동 획득 : Y
관련 : {char['kor']}
의도 : 캐릭터 비밀 및 갈등 요소 인지
내용 :
{char['kor']}의 소개 단계 비밀 정보
HTML :
<div class="story-content">
  <div class="document-page type-secret">
    <div class="section-title">당신의 어두운 면</div>
    <div class="intro-narrative">
{dark_content}
    </div>
  </div>
</div>

"""
    
    clues_content = clues_content[:tag_pos] + new_clues + clues_content[tag_pos:]

with open(clues_path, 'w', encoding='utf-8') as f:
    f.write(clues_content)
    
print("Updated 단서.txt successfully.")
