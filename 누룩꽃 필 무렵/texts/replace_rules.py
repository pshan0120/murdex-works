import re

file_path = r'c:\dev\KLIEN\murdex\works\누룩꽃 필 무렵\texts\단서.txt'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

target = r'당신의 비밀들은 타인에게 추궁받거나 지적받았을 때만 마지못해 이야기 할 수 있습니다\. 하지만 이번 단계에서 모든 비밀을 이야기해야 다음 단계로 진행할 수 있으니, 아무도 당신의 비밀에 대해 묻지 않는다면 대화의 흐름을 자연스럽게 이 주제로 이끌어보세요\. 그럼 누군가는 당신에게 질문을 할 것입니다\.'
replacement = r'당신의 비밀들은 타인에게 추궁받거나 지적받았을 때만 마지못해 이야기 할 수 있습니다. 아무도 당신에게 묻지 않아 이번 단계에서 말하지 못했다면, 이후 단계에서 질문을 받을 때 털어놓을 수 있습니다. 단, 6단계(마지막 단서 단계)가 끝날 때까지는 숨김없이 모두 밝혀야 합니다.'

new_content, count = re.subn(target, replacement, content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f"Replaced {count} occurrences.")
