# -*- coding: utf-8 -*-
"""엔딩_메타.txt(구 엔딩_공통.txt, 조건/ID 색인만 남음) + 변환된 ending_*_lines.json들을
도플로이드의 엔딩_대본.txt와 같은 사람이 읽는 평문 대본 형식으로 합쳐서 texts/엔딩_대본.txt를 만든다.
※ 주의: 대사 본문은 ending_*_lines.json에서 가져오지 엔딩_대본.txt 자체를 읽지 않는다.
   즉 사용자가 엔딩_대본.txt를 직접 고친 뒤 이 스크립트를 다시 돌리면, 그 수정사항이
   반영되지 않은 옛 JSON 스냅샷으로 덮어써진다. 최초 생성 이후에는 함부로 재실행하지 말 것 —
   사용자의 대본 수정은 별도 파서로 DB에 반영해야 한다(convert_endings.py 상단 주석 참고)."""
import re, json, sys
sys.path.append(r"C:\dev\KLIEN\murdex\works\바스타즈 오브 더 유니버스\texts\script_migration")
from script_utils import load_role_map

TXT_PATH = r"C:\dev\KLIEN\murdex\works\바스타즈 오브 더 유니버스\texts\엔딩_메타.txt"
MIG_DIR = r"C:/dev/KLIEN/murdex/works/바스타즈 오브 더 유니버스/texts/script_migration"
OUT_PATH = r"C:\dev\KLIEN\murdex\works\바스타즈 오브 더 유니버스\texts\엔딩_대본.txt"

name_to_role_id, ordered_role_ids = load_role_map()
role_id_to_name = {r_id: name for name, r_id in name_to_role_id.items()}
with open(r"C:\dev\KLIEN\murdex\works\바스타즈 오브 더 유니버스\texts\_role_id_map.json", encoding="utf-8") as f:
    roles = json.load(f)  # role_name(직함), character_name, role_order 순서 보존용

with open(TXT_PATH, encoding="utf-8") as f:
    full = f.read()

# 엔딩별 메타(제목/EndingID/엔딩타입/조건/순서) 블록 추출 — 순서(순서: N) 기준 정렬
blocks = re.split(r'\n<!-- =+ -->\n<!-- Ending \d+\.', full)
metas = []
for block in blocks:
    m = re.search(
        r'제목:\s*(?P<title>.+?)\n'
        r'EndingID\s*:\s*(?P<id>\S+)\n'
        r'엔딩타입:\s*(?P<type>\S+)\n'
        r'조건:\s*(?P<cond>.+?)\n'
        r'순서:\s*(?P<order>\d+)',
        block
    )
    if m:
        metas.append(m.groupdict())
metas.sort(key=lambda d: int(d["order"]))

header = '''※ 대본화 작업 모음. 기존 엔딩_공통.txt(현재 엔딩_메타.txt)의 각 엔딩을 대본 형식으로 재집필해 순서대로 모아둡니다.
※ 조건/ID 등 메타 정보 출처: works/바스타즈 오브 더 유니버스/texts/엔딩_메타.txt (내용 본문은 이제 이 파일에만 있습니다)
※ wav 음성은 아직 다루지 않습니다. (텍스트 재집필만 진행 중)
※ "다크 시리어스(엘드리치)"처럼 부활 이후 이름이 바뀌는 화자는, 담당 배우(화자)는 원래 역할(엘드리치) 그대로 두고 화자 표시 HTML만 그 장면의 표기를 따릅니다.
※ 지문/서술 줄의 담당 플레이어는 그 엔딩에서 실제로 대사가 있는 인물들 사이에서 등장 순서대로 고르게 순환 배정했습니다(한 사람에게만 몰리지 않도록).
'''

out_parts = [header]

for meta in metas:
    title = meta["title"]
    safe_name = re.sub(r'[\/:*?"<>|]', '_', title)
    json_path = f'{MIG_DIR}/ending_{safe_name}_lines.json'
    with open(json_path, encoding="utf-8") as f:
        lines = json.load(f)

    # 이 엔딩에서 실제로 대사가 있는 역할만 "화자 역할" 목록에 표기 (전원이 항상 등장하진 않음)
    speaking_role_ids = {l["roleId"] for l in lines if l["speakerType"] == "PLAYER" and l["roleId"]}
    cast_lines = []
    for r in roles:  # role_order 순서 보존
        if r["role_id"] in speaking_role_ids:
            cast_lines.append(f'    - {r["character_name"]} ({r["role_name"]}): PLAYER')

    section = []
    section.append(f'<!-- ============================================ -->')
    section.append(f'<!-- Ending {meta["order"]}. {title} -->')
    section.append(f'<!-- ============================================ -->')
    section.append('')
    section.append(f'제목: {title}')
    section.append(f'EndingID : {meta["id"]}')
    section.append(f'엔딩타입: {meta["type"]}')
    section.append(f'조건: {meta["cond"]}')
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
        else:  # NPC (이번 범위엔 없지만 형식은 갖춰둠)
            entry.append(f'    화자: (NPC)')
            owner_name = role_id_to_name.get(l["ownerRoleId"], "?")
            entry.append(f'    담당 플레이어: {owner_name}')
            entry.append(f'    대사: {l["lineHtml"]}')
        section.append('\n'.join(entry))
        section.append('')

    out_parts.append('\n'.join(section))

with open(OUT_PATH, "w", encoding="utf-8") as f:
    f.write('\n\n'.join(out_parts))

print(f"Wrote {OUT_PATH}, {len(metas)} endings")
