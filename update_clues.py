import re
import os

file_path = r'd:\dev\murdex-works\바스타즈 오브 더 유니버스\top-down\단서.txt'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Original clue_03 block
# Note: Using regex to match the block more flexibly
clue_03_pattern = r'\[clue_03\][\s\S]*?내용 : 슬리더에게 도착한 협박 쪽지 및 마력석\. \(바스타즈에 들어오기 전, 골든 킹과 거래하고 있었다는 증거인 지령서 / 말리스가 가지고 있다면 전투력 \+8\)'

new_clue_03_04 = """[clue_03]
이름 : 슬리더: 협박 쪽지
유형 : 물증
단계 : 역할 보유
소모AP : 0
정렬순서 : 30
중요도 : 높음
핵심 단서 여부 : Y
교환 가능 여부 : N
획득 가능 여부 : N
획득 조건 존재 여부 : N
획득 조건 내용 : 없음
시작 표시 상태 : 앞면
단계 시작시 자동 획득 : Y
관련 : 슬리더
의도 : 개인별 비밀 및 동기 부여
내용 : 슬리더에게 도착한 협박 쪽지. (바스타즈에 들어오기 전, 골든 킹과 거래하고 있었다는 증거인 지령서)

[clue_04]
이름 : 마력석
유형 : 물증
단계 : 역할 보유
소모AP : 0
정렬순서 : 40
중요도 : 높음
핵심 단서 여부 : Y
교환 가능 여부 : N
획득 가능 여부 : N
획득 조건 존재 여부 : N
획득 조건 내용 : 없음
시작 표시 상태 : 앞면
단계 시작시 자동 획득 : Y
관련 : 슬리더
의도 : 캐릭터 능력치 보정 아이템
내용 : 슬리더가 소지하고 있는 신비한 마력석. (말리스가 가지고 있다면 전투력 +8)"""

match = re.search(clue_03_pattern, content)
if match:
    prefix = content[:match.start()]
    suffix = content[match.end():]
    
    # Increment IDs and Sort Orders in the suffix
    def increment_id(m):
        return f'[clue_{int(m.group(1)) + 1:02d}]'
    
    def increment_order(m):
        return f'정렬순서 : {int(m.group(1)) + 10}'
    
    suffix = re.sub(r'\[clue_(\d+)\]', increment_id, suffix)
    suffix = re.sub(r'정렬순서 : (\d+)', increment_order, suffix)
    
    new_content = prefix + new_clue_03_04 + suffix
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Update successful.")
else:
    print("Pattern not found.")
