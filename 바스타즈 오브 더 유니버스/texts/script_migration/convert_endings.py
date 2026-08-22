# -*- coding: utf-8 -*-
"""[사용 중단 — 2026-08-21] 이 스크립트는 엔딩_공통.txt(현재 엔딩_메타.txt로 개명)의 '내용:'
HTML 본문에서 대사를 뽑아 변환하던 최초 버전입니다. 이제 그 본문 칸은 포인터 문구만 남기고
비워졌고(실제 대사는 엔딩_대본.txt로 옮겨짐), 이 파일은 그 사실을 감지하면 에러를 내고 멈춥니다.
엔딩_대본.txt를 고친 뒤 DB에 반영하려면 그 평문 대본 형식을 읽는 새 파서가 필요합니다(아직 없음,
필요해지면 새로 작성). 이 파일은 과거 변환 이력 참고용으로만 남겨둡니다.
사용법: python convert_endings.py            # 전체 13개
        python convert_endings.py "감춰진 얼굴"  # 지정한 엔딩 1개만 (파일럿/검수용)
"""
import re, json, sys
sys.path.append(r"C:\dev\KLIEN\murdex\works\바스타즈 오브 더 유니버스\texts\script_migration")
from script_utils import load_role_map, strip_wrapping_quotes, resolve_role, RoundRobin

BACKUP_JSON = r"C:\dev\KLIEN\murdex\works\바스타즈 오브 더 유니버스\texts\backup\db_state_원본(수정전).json"
LIVE_TXT = r"C:\dev\KLIEN\murdex\works\바스타즈 오브 더 유니버스\texts\엔딩_메타.txt"
OUT_DIR = r"C:\dev\KLIEN\murdex\works\바스타즈 오브 더 유니버스\texts\script_migration"


def load_live_ending_stories():
    """backup json은 ending_id 조회용으로만 쓰고, 실제 본문은 현재(수정된) 엔딩_메타.txt에서
    매번 새로 뽑는다 — 원문을 고친 뒤 재변환할 때 옛 백업 내용으로 덮어써지는 걸 방지.
    단, 2026-08-21 이후 엔딩_메타.txt의 '내용:' 칸은 포인터 문구만 남아 있으므로, 그걸
    실제 대본으로 오인해 변환하지 않도록 감지되면 즉시 에러를 낸다."""
    with open(LIVE_TXT, encoding="utf-8") as f:
        full = f.read()
    stories = {}
    blocks = re.split(r'\n<!-- =+ -->\n<!-- Ending \d+\.', full)
    for block in blocks:
        m = re.search(r'제목:\s*(.+?)\n.*?내용:\n(.*?)\n(?=<!-- =+ -->|\Z)', block, re.S)
        if m:
            title, body = m.group(1).strip(), m.group(2).strip()
            if '대본으로 이전됨' in body:
                raise RuntimeError(
                    f"'{title}' 엔딩의 내용이 포인터 문구만 남아있습니다(엔딩_대본.txt로 이전됨). "
                    "이 스크립트로는 더 이상 변환할 수 없습니다 — 엔딩_대본.txt용 파서가 필요합니다."
                )
            stories[title] = body
    return stories

LINE_RE = re.compile(
    r'<div class="script-line">\s*'
    r'<span class="script-character">(?P<label>.*?)</span>:\s*'
    r'(?P<content>.*?)\s*'
    r'</div>',
    re.S
)


def clean_html(html):
    html = re.sub(r'<div class="reading-guide">.*?</div>\s*', '', html, flags=re.S)
    html = re.sub(r'<div class="ending-result">.*?</div>\s*', '', html, flags=re.S)
    html = html.replace('<details class="ending-details">', '').replace('</details>', '')
    html = re.sub(r'<summary class="suspense-msg">(.*?)</summary>', r'<p class="suspense-msg">\1</p>', html, flags=re.S)
    return html


def extract_paragraphs(chunk):
    beats = []
    for qm in re.finditer(r'<div class="quote-box">\s*(.*?)\s*</div>', chunk, re.S):
        beats.append(qm.group(1).strip())
    chunk = re.sub(r'<div class="quote-box">.*?</div>', '', chunk, flags=re.S)
    for pm in re.finditer(r'<p(?:\s+class="[^"]*")?>\s*(.*?)\s*</p>', chunk, re.S):
        beats.append(pm.group(1).strip())
    chunk_wo_p = re.sub(r'<p(?:\s+class="[^"]*")?>.*?</p>', '', chunk, flags=re.S)
    for dm in re.finditer(r'<div class="script-direction">\s*(.*?)\s*</div>', chunk_wo_p, re.S):
        beats.append(dm.group(1).strip())
    return [b for b in beats if b]


def convert_one(ending, name_to_role_id, ordered_role_ids=None):
    html = clean_html(ending["ending_story"])

    tokens = []
    last_end = 0
    for m in LINE_RE.finditer(html):
        if m.start() > last_end:
            tokens.append(("text", html[last_end:m.start()]))
        tokens.append(("dialogue", m))
        last_end = m.end()
    if last_end < len(html):
        tokens.append(("text", html[last_end:]))

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
            for beat in extract_paragraphs(val):
                lines.append({
                    "lineOrder": order, "speakerType": "DIRECTIVE",
                    "roleId": None, "npcId": None, "ownerRoleId": rr.next_owner(),
                    "speakerLabelHtml": None, "lineHtml": beat,
                    "audioUrl": None
                })
                order += 1
    return lines, warnings


def main():
    name_to_role_id, ordered_role_ids = load_role_map()
    live_stories = load_live_ending_stories()

    target = sys.argv[1] if len(sys.argv) > 1 else None
    names = [target] if target else list(live_stories.keys())
    missing = [n for n in names if n not in live_stories]
    if missing:
        print(f"ERROR: not found in live 엔딩_공통.txt: {missing}")
        return
    endings = [{"ending_name": n, "ending_story": live_stories[n]} for n in names]

    all_warnings = []
    for e in endings:
        lines, warnings = convert_one(e, name_to_role_id, ordered_role_ids)
        all_warnings += [(e["ending_name"], w) for w in warnings]
        safe_name = re.sub(r'[\\/:*?"<>|]', '_', e["ending_name"])
        out_path = f'{OUT_DIR}\\ending_{safe_name}_lines.json'
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(lines, f, ensure_ascii=False, indent=2)
        print(f'{e["ending_name"]}: {len(lines)} lines -> {out_path}')

    if all_warnings:
        print("\n=== WARNINGS ===")
        for name, w in all_warnings:
            print(f'[{name}] {w}')


if __name__ == "__main__":
    main()
