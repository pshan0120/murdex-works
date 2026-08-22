# -*- coding: utf-8 -*-
"""대사가 있는 단계 3개(대면/막간 I/막간 II)를 엔딩_대본.txt와 같은 형식의
사람이 읽는 평문 대본 문서로 합쳐서 texts/단계_대본.txt를 만든다."""
import json, sys
sys.path.append(r"C:\dev\KLIEN\murdex\works\바스타즈 오브 더 유니버스\texts\script_migration")
from script_utils import load_role_map

OUT_PATH = r"C:\dev\KLIEN\murdex\works\바스타즈 오브 더 유니버스\texts\단계_대본.txt"

with open(r"C:\dev\KLIEN\murdex\works\바스타즈 오브 더 유니버스\texts\_role_id_map.json", encoding="utf-8") as f:
    roles = json.load(f)
role_id_to_name = {r["role_id"]: r["character_name"] for r in roles}

steps = [
    {"order": 2, "name": "대면", "step_id": "854e7234-0cf5-49ae-aeae-ec6a6ade59b3",
     "json": "step2_대면_lines.json"},
    {"order": 3, "name": "막간 I", "step_id": "b74329e3-4ed5-4770-aa5f-a439a1bcb210",
     "json": "step3_막간1_lines.json"},
    {"order": 7, "name": "막간 II", "step_id": "08f3639d-f9c4-4a08-bde6-5295c6559141",
     "json": "step7_막간2_lines.json"},
]

header = '''※ 대본화 작업 모음. 대사가 있는 단계(대면/막간 I/막간 II) 3개를 대본 형식으로 재집필해 순서대로 모아둡니다.
※ 원본: works/바스타즈 오브 더 유니버스/texts/단계_2_대면.txt, 단계_3_막간_1.txt, 단계_7_막간_2.txt
※ wav 음성은 아직 다루지 않습니다. (텍스트 재집필만 진행 중)
※ 게임 진행상 필요한 안내문(예: 막간 I의 조 편성 가이드)은 별도 삽입블록이 아니라, 그 지점의 DIRECTIVE 대사 안에 그대로 이어 붙였습니다. 같은 내용을 단계 설명 HTML 쪽에 중복해서 남겨두지 않습니다.
※ 지문/서술 줄의 담당 플레이어는 그 단계에서 실제로 대사가 있는 인물들 사이에서 등장 순서대로 고르게 순환 배정했습니다(한 사람에게만 몰리지 않도록).
'''

out_parts = [header]

for step in steps:
    with open(step["json"], encoding="utf-8") as f:
        lines = json.load(f)

    speaking_role_ids = {l["roleId"] for l in lines if l["speakerType"] == "PLAYER" and l["roleId"]}
    cast_lines = []
    for r in roles:
        if r["role_id"] in speaking_role_ids:
            cast_lines.append(f'    - {r["character_name"]} ({r["role_name"]}): PLAYER')

    section = []
    section.append(f'<!-- ============================================ -->')
    section.append(f'<!-- Step {step["order"]}. {step["name"]} -->')
    section.append(f'<!-- ============================================ -->')
    section.append('')
    section.append(f'단계 이름: {step["name"]}')
    section.append(f'순서: {step["order"]}')
    section.append(f'StepID : {step["step_id"]}')
    section.append('')
    section.append('화자 역할:')
    section.extend(cast_lines)
    section.append('')
    section.append('대본')
    section.append('')

    for i, l in enumerate(lines, start=1):
        entry = [f'[{i}] 화자 타입: {l["speakerType"]}']
        if l["speakerType"] == "PLAYER":
            entry.append(f'    화자: {role_id_to_name.get(l["roleId"], "?")}')
            entry.append(f'    화자 표시 HTML: {l["speakerLabelHtml"]}')
            entry.append(f'    대사: {l["lineHtml"]}')
        elif l["speakerType"] == "DIRECTIVE":
            owner_name = role_id_to_name.get(l["ownerRoleId"], "?")
            entry.append(f'    담당 플레이어: {owner_name}')
            entry.append(f'    대사: {l["lineHtml"]}')
        else:
            entry.append(f'    화자: (NPC)')
            owner_name = role_id_to_name.get(l["ownerRoleId"], "?")
            entry.append(f'    담당 플레이어: {owner_name}')
            entry.append(f'    대사: {l["lineHtml"]}')
        section.append('\n'.join(entry))
        section.append('')

    out_parts.append('\n'.join(section))

with open(OUT_PATH, "w", encoding="utf-8") as f:
    f.write('\n\n'.join(out_parts))

print(f"Wrote {OUT_PATH}, {len(steps)} steps")
