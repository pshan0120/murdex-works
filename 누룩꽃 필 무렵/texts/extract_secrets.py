import os
import re

base_dir = r"c:\dev\KLIEN\murdex\works\누룩꽃 필 무렵\texts"
# Active code page 65001 output showed:
# 역할_1_백서연.txt
# 역할_2_류현수.txt
# 역할_3_박단희.txt
# 역할_4_정해준.txt
# 역할_5_최도훈.txt
# 역할_6_강은지.txt
roles = [
    ("1_백서연", "백서연"),
    ("2_류현수", "류현수"),
    ("3_박단희", "박단희"),
    ("4_정해준", "정해준"),
    ("5_최도훈", "최도훈"),
    ("6_강은지", "강은지")
]

output_file = os.path.join(base_dir, "단서.txt")

clue_template = """
### [clue_p_{role_en}_{stage_num}_{type_en}]
이름 : [개인] {role_name}의 {type_ko} ({stage_name})
유형 : 정보
단계 : {stage_name}
소모AP : 0
정렬순서 : 100
중요도 : 보통
핵심 단서 여부 : N
교환 가능 여부 : N
획득 가능 여부 : N
획득 조건 존재 여부 : N
획득 조건 내용 : 없음
시작 표시 상태 : 뒷면
단계 시작시 자동 획득 : Y
관련 : {role_name}
의도 : 캐릭터 개인의 속마음 및 정보
내용 :
해당 단계에서 캐릭터가 알고 있는 정보 또는 숨기고 있는 비밀.
HTML :
<div class="story-content">
  <div class="document-page type-{css_class}">
    <div class="document-body small">
{inner_html}
    </div>
  </div>
</div>
이미지생성용 프롬프트: 없음
장소 : 없음
파일명 : p_{role_name}_{stage_name}_{type_ko}
"""

role_en_map = {
    "백서연": "seoyeon",
    "강은지": "eunji",
    "최도훈": "dohun",
    "정해준": "haejun",
    "박단희": "danhee",
    "류현수": "hyunsu"
}

stage_pattern = re.compile(r'\[(\d+)단계:\s*(.+?)\]')

appended_text = "\n\n"

for role_id, role_name in roles:
    file_path = os.path.join(base_dir, f"역할_{role_id}.txt")
    if not os.path.exists(file_path):
        print(f"Skipping {file_path}, not found.")
        continue
    
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    parts = stage_pattern.split(text)
    
    for i in range(1, len(parts), 3):
        stage_num = parts[i]
        stage_name = parts[i+1].strip()
        
        stage_content = parts[i+2]
        
        # 아는 것
        know_match = re.search(r'<summary>\s*당신이 아는 것.*?</summary>\s*<div class="collapsible-content">\s*(.*?)\s*</div>\s*</details>', stage_content, re.DOTALL)
        if know_match:
            inner_html = know_match.group(1).strip()
            inner_html = "\n".join(["      " + line for line in inner_html.split("\n")])
            clue_text = clue_template.format(
                role_en=role_en_map[role_name],
                stage_num=stage_num,
                type_en="know",
                role_name=role_name,
                type_ko="아는 것",
                stage_name=f"{stage_num}단계",
                css_class="knowledge",
                inner_html=inner_html
            )
            appended_text += clue_text
            
        # 비밀
        secret_match = re.search(r'<summary>\s*당신의 비밀.*?</summary>\s*<div class="collapsible-content">\s*(.*?)\s*</div>\s*</details>', stage_content, re.DOTALL)
        if secret_match:
            inner_html = secret_match.group(1).strip()
            inner_html = "\n".join(["      " + line for line in inner_html.split("\n")])
            clue_text = clue_template.format(
                role_en=role_en_map[role_name],
                stage_num=stage_num,
                type_en="secret",
                role_name=role_name,
                type_ko="비밀",
                stage_name=f"{stage_num}단계",
                css_class="secret",
                inner_html=inner_html
            )
            appended_text += clue_text

with open(output_file, 'a', encoding='utf-8') as f:
    f.write(appended_text)

print("Extraction and appending complete.")
