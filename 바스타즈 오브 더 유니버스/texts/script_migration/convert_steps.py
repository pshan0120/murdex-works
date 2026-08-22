# -*- coding: utf-8 -*-
"""[사용 중단 — 2026-08-21] 남은 두 단계(막간 I, 막간 II)를 story_step_script_line 배열로
변환하던 최초 버전. 엔딩과 달리 단계는 설명 HTML 전체가 아니라 script-container 구간만 대본으로
옮기고 나머지는 POST_SCRIPT 마커로 자르는 방식이었다.
※ 2026-08-21 이후 단계_3_막간_1.txt/단계_7_막간_2.txt 원본의 script-container를 실제로
   POST_SCRIPT로 교체했기 때문에, 이 스크립트가 읽어올 소스 자체가 더 이상 없다(__main__ 블록은
   더 이상 재실행할 수 없음 — 대본 원본은 이제 단계_대본.txt). 다만 convert_fragment()/RoundRobin
   관련 함수는 다른 스크립트에서 계속 재사용하므로 그대로 남겨둔다.
"""
import re, json, sys
sys.path.append(r"C:\dev\KLIEN\murdex\works\바스타즈 오브 더 유니버스\texts\script_migration")
from script_utils import load_role_map, strip_wrapping_quotes, resolve_role, RoundRobin, extract_balanced_div

OUT_DIR = r"C:\dev\KLIEN\murdex\works\바스타즈 오브 더 유니버스\texts\script_migration"

LINE_RE = re.compile(
    r'<div class="script-line">\s*'
    r'<span class="script-character">(?P<label>.*?)</span>:\s*'
    r'(?P<content>.*?)\s*'
    r'</div>',
    re.S
)


def convert_fragment(html_fragment, name_to_role_id, ordered_role_ids=None):
    """script-container(대사)와 그 사이/앞뒤의 standalone script-direction(지문)을
    등장 순서 그대로 PLAYER/DIRECTIVE 줄로 변환한다."""
    tokens = []
    last_end = 0
    for m in LINE_RE.finditer(html_fragment):
        if m.start() > last_end:
            tokens.append(("text", html_fragment[last_end:m.start()]))
        tokens.append(("dialogue", m))
        last_end = m.end()
    if last_end < len(html_fragment):
        tokens.append(("text", html_fragment[last_end:]))

    rr = RoundRobin(fallback_pool=ordered_role_ids)
    for kind, val in tokens:
        if kind == "dialogue":
            rid, _ = resolve_role(val.group("label"), name_to_role_id)
            rr.note_speaker(rid)

    lines, order, warnings = [], 0, []
    for kind, val in tokens:
        if kind == "dialogue":
            role_id, label_html = resolve_role(val.group("label"), name_to_role_id)
            if not role_id:
                warnings.append(f'unresolved speaker label: {val.group("label")}')
                continue
            lines.append({
                "lineOrder": order, "speakerType": "PLAYER",
                "roleId": role_id, "npcId": None, "ownerRoleId": role_id,
                "speakerLabelHtml": label_html,
                "lineHtml": strip_wrapping_quotes(val.group("content")),
                "audioUrl": None
            })
            order += 1
        else:
            for dm in re.finditer(r'<div class="script-direction">\s*(.*?)\s*</div>', val, re.S):
                beat = dm.group(1).strip()
                if beat:
                    lines.append({
                        "lineOrder": order, "speakerType": "DIRECTIVE",
                        "roleId": None, "npcId": None, "ownerRoleId": rr.next_owner(),
                        "speakerLabelHtml": None, "lineHtml": beat,
                        "audioUrl": None
                    })
                    order += 1
    return lines, warnings


if __name__ == "__main__":
    raise RuntimeError(
        "이 스크립트는 더 이상 실행할 수 없습니다 — 단계_3_막간_1.txt/단계_7_막간_2.txt의 "
        "script-container가 이미 POST_SCRIPT로 교체되어 소스가 남아있지 않습니다. "
        "대본을 고치려면 단계_대본.txt를 수정한 뒤 별도 파서로 DB에 반영하세요."
    )

    name_to_role_id, _ = load_role_map()

    # 단계 3: 막간 I — 전체가 하나의 script-container(+ 앞뒤 standalone script-direction 2개)
    # 반드시 현재(수정된) 살아있는 .txt에서 읽는다 — backup/ 원본은 최초 스냅샷이라 이후 수정사항이 반영 안 됨.
    with open(r"C:\dev\KLIEN\murdex\works\바스타즈 오브 더 유니버스\texts\단계_3_막간_1.txt", encoding="utf-8") as f:
        step3_text = f.read()
    start = step3_text.index('<div class="script-container">')
    end = extract_balanced_div(step3_text, start)
    inner_start = step3_text.index('>', start) + 1
    fragment = step3_text[inner_start:end - len('</div>')]
    lines, warnings = convert_fragment(fragment, name_to_role_id)
    print(f"막간 I: {len(lines)} lines, warnings={warnings}")
    with open(f'{OUT_DIR}\\step3_막간1_lines.json', "w", encoding="utf-8") as f:
        json.dump(lines, f, ensure_ascii=False, indent=2)

    # 단계 7: 막간 II — 첫 guide-box 다음에 나오는 script-container 전체 (마찬가지로 현재 파일에서 읽음)
    with open(r"C:\dev\KLIEN\murdex\works\바스타즈 오브 더 유니버스\texts\단계_7_막간_2.txt", encoding="utf-8") as f:
        step7_text = f.read()
    start = step7_text.index('<div class="script-container">')
    end = extract_balanced_div(step7_text, start)
    inner_start = step7_text.index('>', start) + 1
    fragment = step7_text[inner_start:end - len('</div>')]
    lines, warnings = convert_fragment(fragment, name_to_role_id)
    print(f"막간 II: {len(lines)} lines, warnings={warnings}")
    with open(f'{OUT_DIR}\\step7_막간2_lines.json', "w", encoding="utf-8") as f:
        json.dump(lines, f, ensure_ascii=False, indent=2)
