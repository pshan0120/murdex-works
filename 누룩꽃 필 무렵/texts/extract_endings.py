import os
import re

base_dir = r"c:\dev\KLIEN\murdex\works\누룩꽃 필 무렵\texts"
roles = [
    ("1_백서연", "백서연", "seoyeon"),
    ("2_류현수", "류현수", "hyunsu"),
    ("3_박단희", "박단희", "danhee"),
    ("4_정해준", "정해준", "haejun"),
    ("5_최도훈", "최도훈", "dohun"),
    ("6_강은지", "강은지", "eunji")
]

output_file = os.path.join(base_dir, "단서.txt")

clue_template = """
### [clue_p_{role_en}_ending]
이름 : [개인] {role_name}의 자백 (종막)
유형 : 정보
단계 : 마지막 단서 단계
소모AP : 0
정렬순서 : 999
중요도 : 높음
핵심 단서 여부 : N
교환 가능 여부 : N
획득 가능 여부 : N
획득 조건 존재 여부 : Y
획득 조건 내용 : 암호코드 '{passcode}' 입력
시작 표시 상태 : 뒷면
단계 시작시 자동 획득 : N
관련 : {role_name}
의도 : 최종 자백
내용 :
{role_name}의 최종 자백 진술서.
HTML :
<div class="story-content">
  <div class="document-page type-confession">
    <h3>수사 협조 진술서 (작성자: {role_name})</h3>
    <div class="document-body">
{inner_html}
    </div>
  </div>
</div>
이미지생성용 프롬프트: 없음
장소 : 없음
파일명 : p_{role_name}_자백
"""

appended_text = "\n\n"

# Regex to capture the passcode from "암호 코드 [미스터리]가 불리기 전까지..."
passcode_pattern = re.compile(r'암호 코드\s*\[(.*?)\]\s*[가이]\s*불리기 전까지')
# Regex to capture the confession text
confession_pattern = re.compile(r'<div class="confession-box">.*?<p class="confession-speech">\s*(.*?)\s*</p>', re.DOTALL)

for role_id, role_name, role_en in roles:
    file_path = os.path.join(base_dir, f"역할_{role_id}.txt")
    if not os.path.exists(file_path):
        print(f"Skipping {file_path}, not found.")
        continue
    
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    pass_match = passcode_pattern.search(text)
    if pass_match:
        passcode = pass_match.group(1).strip()
    else:
        print(f"Passcode not found in {file_path}")
        continue
        
    conf_match = confession_pattern.search(text)
    if conf_match:
        confession_text = conf_match.group(1).strip()
        # Convert newline + spaces to paragraph tags or just br? The text has literal newlines, let's wrap them or format.
        # But wait, the original text is just a block of text separated by newlines.
        # Let's replace newlines with <br><br> for the confession text.
        lines = [line.strip() for line in confession_text.split('\n') if line.strip()]
        formatted_html = "\n".join([f"      <p>{line}</p>" for line in lines])
        
        clue_text = clue_template.format(
            role_en=role_en,
            role_name=role_name,
            passcode=passcode,
            inner_html=formatted_html
        )
        appended_text += clue_text
    else:
        print(f"Confession not found in {file_path}")

with open(output_file, 'a', encoding='utf-8') as f:
    f.write(appended_text)

print("Extraction and appending of confessions complete.")
