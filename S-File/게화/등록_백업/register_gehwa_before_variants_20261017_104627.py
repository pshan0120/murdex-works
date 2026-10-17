"""게화(S-File: 게화) 콘텐츠를 works/S-File/게화/texts 의 확정 텍스트에서 읽어 DB에 등록한다.

- story 행(작품 껍데기)은 이미 있다. 제목, 카테고리, 가격, 표지, 연령, 태그 등 작가가 정한 값은 건드리지 않고
  소개(description), 요약(summary), 로비 가이드, 커스텀 CSS 만 텍스트 기준으로 갱신한다.
- 역할, 단계, 대본, 단서 그룹, 단서(변형, 표시 규칙, 자동 지급, 연계, 접근 조건), 질문, 엔딩(+대본), NPC 를 새로 만든다.
- 이미 콘텐츠가 있으면 중단한다(중복 등록 방지). 방(room), 구매(purchase)는 건드리지 않는다.
- 컷씬(intro_cutscenes)과 이미지, 음성은 아직 없으므로 등록하지 않는다.
- 채점표(rubric)는 질문 ID 가 필요하므로 이 스크립트가 만든 ID 매핑(등록_ID매핑.json)으로 따로 등록한다.

단서 매핑 규칙(누룩꽃, 도플로이드의 기존 등록 방식과 같다):
  - 자동 지급(앞면): is_hidden_possession=1, 획득 불가, clue_auto_ownership(단계, 역할), 표시 규칙 (처음, HIDDEN)
  - 뒷면(암호, 연계 보조): 보드에 뒷면으로 놓였다가 조사한 사람만 개인 소유하는 단서(획득 가능, 공개 불가, 교환 불가).
    표시 규칙 (처음, HIDDEN) + (단계, VISIBLE_BACK),
    관련 역할만 조사하도록 ALLOWED_ROLE 접근 조건을 건다. 암호는 variant.passcodes 에 담는다.
  - 연계 보조(조사하면 뒷면으로 추가): 트리거가 암호로 여는 보드 단서(49)인 경우에만 clue_dependency 로 연결한다.
    트리거가 자동 지급 단서인 경우(27, 33, 39)는 조사 이벤트가 발생하지 않아 연계가 동작하지 않으므로,
    해당 단계 시작 시 보드에 뒷면으로 바로 배치한다.

사용법:
  python scripts/register_gehwa.py            # 파싱, 검증만 (DB 접속 없음)
  python scripts/register_gehwa.py --rehearse # 전체를 트랜잭션 안에서 실행한 뒤 ROLLBACK (SQL 검증용)
  python scripts/register_gehwa.py --apply    # 백업 JSON 저장 후 실제 반영(COMMIT)
"""
import argparse
import json
import os
import re
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8")

STORY_ID = "7169e13b-5160-4a9b-9769-8ffd19763aa7"
WORK = r"C:\dev\KLIEN\murdex\works\S-File\게화"
TEXTS = os.path.join(WORK, "texts")
CSS_PATH = os.path.join(WORK, "styles", "게화.css")
MAP_PATH = os.path.join(WORK, "등록_ID매핑.json")
BACKUP_DIR = os.path.join(WORK, "등록_백업")

ROLE_KEYS = {"베일라": "veyla", "마커스": "marcus"}
CLUE_TYPE = {"물증": "PHYSICAL", "증언": "TESTIMONY", "관계": "RELATIONSHIP", "시간": "TIMELINE", "관찰": "OBSERVATION", "통찰": "INSIGHT"}
IMPORTANCE = {"최고": "HIGH", "높음": "HIGH", "보통": "MEDIUM", "낮음": "LOW"}
ENDING_TYPE = {"TRUE_ENDING", "NORMAL_ENDING", "BAD_ENDING", "HIDDEN_ENDING", "EPILOGUE_STORY"}
# 연계 보조 단서 중 트리거가 자동 지급 단서라 의존성이 동작하지 않는 것(보드에 바로 배치한다)
LINKED_PLACED_DIRECT = set()
# 연계 보조 단서 중 트리거가 암호로 여는 보드 단서라 의존성이 동작하는 것: 대상 단서 번호 -> 트리거 단서 번호
LINKED_BY_DEPENDENCY = {31: 27, 38: 33, 45: 39, 52: 49}
# 암호 철자 변형(대소문자)과 같은 뜻의 한글 답("진화"). 영문 암호는 대소문자 변형을 허용한다.
PASSCODE_VARIANTS = {"evolution": ["evolution", "Evolution", "EVOLUTION", "진화"]}


def read(name):
    with open(os.path.join(TEXTS, name), encoding="utf-8") as f:
        return f.read().replace("\r\n", "\n")


def role_key(text):
    for k in ROLE_KEYS:
        if k in text:
            return k
    raise ValueError(f"역할을 알 수 없음: {text!r}")


def field(block, label, required=True, default=None):
    m = re.search(rf"^{re.escape(label)} : ?(.*)$", block, re.M)
    if not m:
        if required:
            raise ValueError(f"필드 없음: {label}")
        return default
    return m.group(1).strip()


def section(text, header_regex, stop_regex):
    """header_regex 가 처음 나오는 줄 다음부터 stop_regex 직전까지."""
    m = re.search(header_regex, text, re.M)
    if not m:
        raise ValueError(f"섹션 없음: {header_regex}")
    rest = text[m.end():]
    s = re.search(stop_regex, rest, re.M)
    return (rest[:s.start()] if s else rest).strip("\n")


# ---------------- 파싱: 역할 ----------------
def parse_role(filename):
    t = read(filename)
    role_id = field(t, "RoleID")
    name = section(t, r"^1\. 역할 이름\s*$", r"^\d+\. ").strip()
    character = section(t, r"^2\. 캐릭터 이름\s*$", r"^\d+\. ").strip()
    order = int(section(t, r"^3\. 역할 순서\s*$", r"^\d+\. ").strip())
    summary_block = section(t, r"^4\. 역할 요약\s*$", r"^\d+\. ")
    summary = summary_block.split("\n")[0].strip()
    public = section(t, r"^6\. 공개 정보\s*$", r"^\d+\. ").strip()
    sheet = section(t, r"^7\. 역할 시트\s*$", r"^\d+\. ").strip()
    secret = section(t, r"^8\. 숨기고 싶은 비밀\s*$", r"^\d+\. ").strip()
    guide_raw = section(t, r"^9\. 단계별 역할 지침\s*$", r"\Z(?!\n)")
    guidelines = {}
    for m in re.finditer(r"^\[([^\]]+)\] \(단계_(\d+)\)\s*\n(.*?)(?=^\[[^\]]+\] \(단계_\d+\)|\Z)", guide_raw, re.M | re.S):
        guidelines[int(m.group(2))] = m.group(3).strip()
    return {"role_id": role_id, "role_name": name, "character": character, "order": order, "summary": summary,
            "public": public, "sheet": sheet, "secret": secret, "guidelines": guidelines, "key": role_key(character)}


# ---------------- 파싱: 단계 ----------------
def parse_script_lines(text):
    """'[n] 화자 타입: ...' 블록 목록. 반환: [{type, owner, speaker, label, text}]"""
    lines = []
    for m in re.finditer(r"^\[(\d+)\] 화자 타입: (\w+)\n(.*?)(?=^\[\d+\] 화자 타입: |\Z)", text, re.M | re.S):
        n, typ, body = int(m.group(1)), m.group(2), m.group(3)
        owner = re.search(r"^\s+담당 플레이어: (.+)$", body, re.M)
        speaker = re.search(r"^\s+화자: (.+)$", body, re.M)
        label = re.search(r"^\s+화자 표시 HTML: (.+)$", body, re.M)
        image = re.search(r"^\s+이미지: (.+)$", body, re.M)
        dialog = re.search(r"^\s+대사: (.*?)\s*\Z", body, re.M | re.S)
        lines.append({
            "n": n, "type": typ, "image": image.group(1).strip() if image else None,
            "owner": owner.group(1).strip() if owner else None,
            "speaker": speaker.group(1).strip() if speaker else None,
            "label": label.group(1).strip() if label else None,
            "text": dialog.group(1).strip() if dialog else None,
        })
    for i, l in enumerate(lines, start=1):
        assert l["n"] == i, f"대본 번호 불연속: {l['n']} (기대 {i})"
        assert l["text"], f"대사 없음: [{l['n']}]"
        assert l["type"] in ("PLAYER", "NPC", "DIRECTIVE"), l["type"]
        if l["type"] == "PLAYER":
            assert l["speaker"] and l["label"], f"PLAYER 화자 누락: [{l['n']}]"
        if l["type"] == "NPC":
            assert l["speaker"] and l["label"] and l["owner"], f"NPC 필드 누락: [{l['n']}]"
        if l["type"] == "DIRECTIVE":
            assert l["owner"], f"DIRECTIVE 담당 누락: [{l['n']}]"
    return lines


def parse_step(filename):
    t = read(filename)
    order = int(section(t, r"^1\. 순서\s*$", r"^\d+\. ").strip())
    name = section(t, r"^2\. 단계 이름\s*$", r"^\d+\. ").strip()
    step_type = section(t, r"^3\. 단계 유형\s*$", r"^\d+\. ").strip()
    dur = section(t, r"^4\. 예상 소요 시간\s*$", r"^\d+\. ").strip()
    m = re.match(r"(\d+)분", dur)
    duration = int(m.group(1)) if m else None
    auto = section(t, r"^5\. 자동 진행 여부\s*$", r"^\d+\. ").strip() == "Y"
    desc = section(t, r"^\d+\. 단계 설명\s*$", r"^\d+\. 대본 관리")
    ap = {}
    am = re.search(r"^\d+\. 지급 AP\s*\n(.*?)(?=^\d+\. )", t, re.M | re.S)
    if am:
        for line in am.group(1).strip().split("\n"):
            lm = re.match(r"(.+?) : (\d+)", line.strip())
            if lm:
                ap[role_key(lm.group(1))] = int(lm.group(2))
    script_text = ""
    sm = re.search(r"^\d+\. 대본 관리[^\n]*\n(.*)\Z", t, re.M | re.S)
    if sm:
        script_text = sm.group(1)
    return {"step_id": field(t, "StepID"), "order": order, "name": name, "type": step_type, "duration": duration,
            "auto": auto, "description": desc, "ap": ap, "script": parse_script_lines(script_text) if "화자 타입:" in script_text else []}


# ---------------- 파싱: 단서 ----------------
def parse_clues():
    t = read("단서.txt")
    parts = re.split(r"^\[clue_(\d+)\]\s*$", t, flags=re.M)[1:]
    clues = []
    for i in range(0, len(parts), 2):
        num, b = int(parts[i]), parts[i + 1]
        stage = field(b, "단계")
        sm = re.search(r"\((베일라|마커스|공통), (\d+)단계\)", stage)
        assert sm, f"단계 파싱 실패: clue_{num}"
        html = re.search(r"^HTML :\n(.*?)\n이미지생성용 프롬프트:", b, re.M | re.S).group(1).strip()
        qm = re.search(r"^질문 HTML :\n(.*?)\n내용 :\n", b, re.M | re.S)
        cond = field(b, "획득 조건 내용")
        pm = re.search(r"암호 '([^']+)' 입력", cond)
        clues.append({
            "num": num,
            "name": field(b, "이름"),
            "group": field(b, "단서 그룹"),
            "type": CLUE_TYPE[field(b, "유형")],
            "importance": IMPORTANCE[field(b, "중요도")],
            "role": sm.group(1),
            "stage": int(sm.group(2)),
            "ap": int(field(b, "소모AP")),
            "order": int(field(b, "정렬순서")),
            "back": field(b, "시작 표시 상태") == "뒷면",
            "auto": field(b, "단계 시작시 자동 획득") == "Y",
            "has_cond": field(b, "획득 조건 존재 여부") == "Y",
            "passcode": pm.group(1) if pm else None,
            "question_html": qm.group(1).strip() if qm else None,
            "html": html,
        })
    return clues


def parse_groups():
    t = read("단서_그룹.txt")
    groups = []
    for m in re.finditer(r"^(\d+)\. (.+?)\nGroupID : .*\n- 파일명: .*\n- 설명: .*\n(?:- 이미지생성용 프롬프트: .*\n)?- HTML:\n([\s\S]*?)(?=^\d+\. |\Z)", t, re.M):
        groups.append({"order": int(m.group(1)), "name": m.group(2).strip(), "html": m.group(3).strip()})
    assert len(groups) == 10, len(groups)
    return groups


# ---------------- 파싱: 질문, 엔딩, 아웃트로, 기본정보 ----------------
def parse_questions():
    out = []
    for fn in sorted(os.listdir(TEXTS)):
        m = re.match(r"질문_개별_(\d+)_(베일라|마커스)_.+\.txt$", fn)
        if not m:
            continue
        t = read(fn)
        start = t.index('<div class="story-content">')
        html = t[start:].strip()
        order = int(re.search(r"질문 순서: (\d+)\.", t).group(1))
        qid = re.search(r"채점/rubric\.json의 문항 (\w+)", t).group(1)
        out.append({"file": fn, "role": m.group(2), "order": order, "html": html, "rubric_id": qid})
    assert len(out) == 6, len(out)
    return out


def parse_ending():
    s = read("엔딩_대본.txt")
    name = re.search(r"^제목: (.+)$", s, re.M).group(1).strip()
    etype = re.search(r"^엔딩타입: (\w+)", s, re.M).group(1)
    assert etype in ENDING_TYPE, etype
    cond = re.search(r"^조건: (.+)$", s, re.M).group(1).strip()
    ending_id = field(s, "EndingID")
    script = parse_script_lines(s[re.search(r"^대본\s*$", s, re.M).end():])
    attach_ending_images(script)
    return {"ending_id": ending_id, "name": name, "type": etype, "condition": cond,
            "story": ending_story_html(script), "script": script}


def attach_ending_images(script):
    """'이미지: 파일명' 줄이 있는 대사 앞에 삽화 <img>를 붙인다. 주소는 등록_엔딩이미지.json (upload_gehwa_ending_images.py)."""
    if not any(l.get("image") for l in script):
        return
    with open(os.path.join(os.path.dirname(TEXTS), "등록_엔딩이미지.json"), encoding="utf-8") as f:
        urls = json.load(f)
    for l in script:
        if l.get("image"):
            assert l["image"] in urls, f"업로드되지 않은 삽화: {l['image']}"
            l["text"] = (f'<img src="{urls[l["image"]]}" alt="" '
                         'width="1024" height="572" style="display:block;width:100%;max-width:560px;height:auto;aspect-ratio:1024/572;margin:0 auto 14px;border-radius:8px;" />'
                         + l["text"])


def ending_story_html(script):
    """엔딩 HTML 본문(NOT NULL 컬럼)은 대본 줄을 순서대로 이어 만든다."""
    paras = []
    for l in script:
        if l["type"] == "DIRECTIVE":
            paras.append(f"  <p>{l['text']}</p>")
        else:
            paras.append(f"  <p>{l['label']} {l['text']}</p>")
    return '<div class="story-content">\n' + "\n".join(paras) + "\n</div>"


def parse_outro():
    return read("아웃트로.txt").strip()


def parse_story_info():
    t = read("기본정보.txt")
    summary = re.search(r"^- 요약: (.+)$", t, re.M).group(1).strip()
    intro = section(t, r"^3\. 상세 소개 \(구매 전 노출용\)\s*$", r"^4\. 룸 로비 가이드")
    lobby = section(t, r"^4\. 룸 로비 가이드[^\n]*\n", r"\Z(?!\n)")
    with open(CSS_PATH, encoding="utf-8") as f:
        css = f.read().replace("\r\n", "\n")
    return {"summary": summary, "description": intro.strip(), "lobby_guide_html": lobby.strip(), "css": css}


def parse_all():
    roles = [parse_role("역할_1_베일라.txt"), parse_role("역할_2_마커스.txt")]
    steps = [parse_step(fn) for fn in sorted(os.listdir(TEXTS), key=lambda x: (0, int(re.match(r"단계_(\d+)", x).group(1))) if x.startswith("단계_") else (1, 0)) if fn.startswith("단계_")]
    for i, s in enumerate(steps, start=1):
        assert s["order"] == i, (s["name"], s["order"])
    assert steps[-1]["type"] == "EPILOGUE"
    clues = parse_clues()
    groups = parse_groups()
    group_names = {g["name"] for g in groups}
    for c in clues:
        assert c["group"] in group_names, f"그룹 없음: {c['group']}"
        assert 1 <= c["stage"] <= 4
        if c["back"]:
            assert not c["auto"], c["num"]
        if c["has_cond"] and not c["passcode"] and c["num"] not in LINKED_PLACED_DIRECT and c["num"] not in LINKED_BY_DEPENDENCY:
            raise AssertionError(f"처리 규칙 없는 접근 조건: clue_{c['num']}")
    for c in clues:
        if c["passcode"]:
            assert c["back"] and c["question_html"], f"암호 단서는 뒷면+질문 HTML 필요: {c['num']}"
    return {"roles": roles, "steps": steps, "clues": clues, "groups": groups, "questions": parse_questions(),
            "ending": parse_ending(), "outro": parse_outro(), "info": parse_story_info()}


# ---------------- 실행 ----------------
def nid():
    return str(uuid.uuid4())


def run(cur, d):
    def one(sql, *a):
        cur.execute(sql, a)
        r = cur.fetchone()
        return list(r.values())[0] if isinstance(r, dict) else r[0]

    # 0) 중복 등록 방지
    for tbl, sql in {
        "role": "SELECT COUNT(*) FROM role WHERE story_id=%s",
        "story_step": "SELECT COUNT(*) FROM story_step WHERE story_id=%s",
        "clue": "SELECT COUNT(*) FROM clue WHERE story_id=%s",
        "clue_group": "SELECT COUNT(*) FROM clue_group WHERE story_id=%s",
        "story_ending": "SELECT COUNT(*) FROM story_ending WHERE story_id=%s",
        "npc_character": "SELECT COUNT(*) FROM npc_character WHERE story_id=%s",
    }.items():
        n = one(sql, STORY_ID)
        assert n == 0, f"이미 콘텐츠가 있음: {tbl}={n}"
    assert one("SELECT COUNT(*) FROM story WHERE story_id=%s", STORY_ID) == 1, "작품 행 없음"
    for r in d["roles"]:
        assert one("SELECT COUNT(*) FROM role WHERE role_id=%s", r["role_id"]) == 0, f"role_id 충돌: {r['role_id']}"
    for s in d["steps"]:
        assert one("SELECT COUNT(*) FROM story_step WHERE step_id=%s", s["step_id"]) == 0, f"step_id 충돌: {s['step_id']}"
    assert one("SELECT COUNT(*) FROM story_ending WHERE ending_id=%s", d["ending"]["ending_id"]) == 0, "ending_id 충돌"

    ids = {"story_id": STORY_ID, "roles": {}, "steps": {}, "groups": {}, "clues": {}, "questions": {}, "npcs": {}}

    # 1) 작품 정보
    info = d["info"]
    cur.execute(
        "UPDATE story SET summary=%s, description=%s, lobby_guide_html=%s, custom_css=%s WHERE story_id=%s",
        (info["summary"], info["description"], info["lobby_guide_html"], info["css"], STORY_ID),
    )

    # 2) 역할 + 비밀
    role_ids = {}
    for r in sorted(d["roles"], key=lambda x: x["order"]):
        rid = r["role_id"]
        role_ids[r["key"]] = rid
        ids["roles"][r["character"]] = rid
        cur.execute(
            "INSERT INTO role (role_id, story_id, role_name, character_name, public_info, role_image_url, role_order, summary, description) "
            "VALUES (%s,%s,%s,%s,%s,NULL,%s,%s,%s)",
            (rid, STORY_ID, r["role_name"], r["character"], r["public"], r["order"], r["summary"], r["sheet"]),
        )
        cur.execute(
            "INSERT INTO role_secret (secret_id, role_id, secret_title, secret_content, importance_level, disclosure_timing, "
            "can_share, share_restriction, secret_order) VALUES (%s,%s,'숨기고 싶은 비밀',%s,'MEDIUM','NEVER',1,'FULL',0)",
            (nid(), rid, r["secret"]),
        )

    # 3) NPC (대본에 나오는 화자 중 PLAYER 가 아닌 이름)
    npc_names = []
    for s in d["steps"]:
        for l in s["script"]:
            if l["type"] == "NPC" and l["speaker"] not in npc_names:
                npc_names.append(l["speaker"])
    for l in d["ending"]["script"]:
        if l["type"] == "NPC" and l["speaker"] not in npc_names:
            npc_names.append(l["speaker"])
    npc_ids = {}
    for i, name in enumerate(npc_names, start=1):
        npc_ids[name] = nid()
        ids["npcs"][name] = npc_ids[name]
        cur.execute("INSERT INTO npc_character (npc_id, story_id, name, npc_order) VALUES (%s,%s,%s,%s)", (npc_ids[name], STORY_ID, name, i))

    # 4) 단계, 지급 AP, 역할 지침, 대본
    step_ids = {}
    for s in d["steps"]:
        sid = s["step_id"]
        step_ids[s["order"]] = sid
        ids["steps"][s["name"]] = sid
        is_final = 1 if s["type"] == "EPILOGUE" else 0
        cur.execute(
            "INSERT INTO story_step (step_id, story_id, step_order, step_name, step_type, description, audio_url, "
            "estimated_duration, is_auto_proceed, outro, is_final_step) VALUES (%s,%s,%s,%s,%s,%s,NULL,%s,%s,%s,%s)",
            (sid, STORY_ID, s["order"], s["name"], s["type"], s["description"], s["duration"], 1 if s["auto"] else 0,
             d["outro"] if is_final else None, is_final),
        )
        for key, ap in s["ap"].items():
            cur.execute(
                "INSERT INTO story_step_role_ap (step_role_ap_id, story_id, step_id, role_id, max_ap) VALUES (%s,%s,%s,%s,%s)",
                (nid(), STORY_ID, sid, role_ids[key], ap),
            )
        for r in d["roles"]:
            g = r["guidelines"].get(s["order"])
            if g:
                cur.execute(
                    "INSERT INTO story_step_role_guideline (guideline_id, step_id, role_id, description) VALUES (%s,%s,%s,%s)",
                    (nid(), sid, r["role_id"], g),
                )
        for i, l in enumerate(s["script"]):
            insert_script_line(cur, "story_step_script_line", "step_id", sid, i, l, role_ids, npc_ids)

    # 5) 단서 그룹
    group_ids = {}
    for g in d["groups"]:
        gid = nid()
        group_ids[g["name"]] = gid
        ids["groups"][g["name"]] = gid
        cur.execute(
            "INSERT INTO clue_group (group_id, story_id, group_name, description, image_url, group_order) VALUES (%s,%s,%s,%s,NULL,%s)",
            (gid, STORY_ID, g["name"], g["html"], g["order"]),
        )

    # 6) 단서
    clue_ids = {}
    for c in d["clues"]:
        clue_ids[c["num"]] = nid()
    for c in d["clues"]:
        cid, vid = clue_ids[c["num"]], nid()
        ids["clues"][f"clue_{c['num']:02d}"] = {"clue_id": cid, "variant_id": vid, "name": c["name"]}
        step_id = step_ids[2 * c["stage"] + 1]  # 조사 단계는 3, 5, 7, 9번(사이마다 추리 단계)
        role_id = role_ids[c["role"]]
        board = c["back"]  # 뒷면 = 게임보드 단서
        cur.execute(
            "INSERT INTO clue (clue_id, story_id, group_id, clue_type, importance_level, is_revealable, is_exchangeable, "
            "is_hidden_possession, ap_cost, clue_order, is_acquirable, is_disposable_read, has_acquisition_condition) "
            "VALUES (%s,%s,%s,%s,%s,0,0,%s,%s,%s,%s,0,%s)",
            (cid, STORY_ID, group_ids[c["group"]], c["type"], c["importance"],
             0 if board else 1, c["ap"], c["order"], 1 if board else 0, 1 if board else 0),
        )
        passcodes = None
        if c["passcode"]:
            passcodes = PASSCODE_VARIANTS.get(c["passcode"], [c["passcode"]])
        cur.execute(
            "INSERT INTO clue_variant (variant_id, clue_id, clue_name, variant_type, clue_content, clue_image_url, is_default, "
            "passcodes, passcode_ap_cost, passcode_question_html, priority) VALUES (%s,%s,%s,'DEFAULT',%s,NULL,1,%s,0,%s,0)",
            (vid, cid, c["name"], c["html"], json.dumps(passcodes, ensure_ascii=False) if passcodes else None, c["question_html"]),
        )
        if board:
            cur.execute(
                "INSERT INTO clue_acquisition_condition (condition_id, variant_id, condition_type, target_value) VALUES (%s,%s,'ALLOWED_ROLE',%s)",
                (nid(), vid, role_id),
            )
            cur.execute(
                "INSERT INTO clue_display_state_rule (rule_id, clue_id, trigger_step_id, target_display_state, variant_id) VALUES (%s,%s,NULL,'HIDDEN',NULL)",
                (nid(), cid),
            )
            if c["num"] not in LINKED_BY_DEPENDENCY:
                cur.execute(
                    "INSERT INTO clue_display_state_rule (rule_id, clue_id, trigger_step_id, target_display_state, variant_id) VALUES (%s,%s,%s,'VISIBLE_BACK',%s)",
                    (nid(), cid, step_id, vid),
                )
        else:
            cur.execute(
                "INSERT INTO clue_display_state_rule (rule_id, clue_id, trigger_step_id, target_display_state, variant_id) VALUES (%s,%s,NULL,'HIDDEN',NULL)",
                (nid(), cid),
            )
            assert c["auto"], f"앞면 단서는 자동 지급이어야 함: clue_{c['num']}"
            cur.execute(
                "INSERT INTO clue_auto_ownership (auto_ownership_id, clue_id, trigger_step_id, target_role_id) VALUES (%s,%s,%s,%s)",
                (nid(), cid, step_id, role_id),
            )
    for target, trigger in LINKED_BY_DEPENDENCY.items():
        cur.execute(
            "INSERT INTO clue_dependency (dependency_id, trigger_clue_id, target_clue_id, trigger_type, effect_type, trigger_variant_id) "
            "VALUES (%s,%s,%s,'INVESTIGATE','HIDDEN_TO_BACK',NULL)",
            (nid(), clue_ids[trigger], clue_ids[target]),
        )

    # 7) 질문 (최종 결론 단계, 역할별 주관식)
    final_q_step = next(s for s in d["steps"] if s["type"] == "CONCLUSION")["step_id"]
    for q in sorted(d["questions"], key=lambda x: (x["role"], x["order"])):
        qid = nid()
        ids["questions"][q["rubric_id"]] = qid
        cur.execute(
            "INSERT INTO question (question_id, step_id, role_id, title, is_multiple_choice, is_vote, allow_tie, show_result_after_submit, "
            "is_required, question_order, answer_max_length) VALUES (%s,%s,%s,%s,0,0,1,0,1,%s,1000)",
            (qid, final_q_step, role_ids[q["role"]], q["html"], q["order"]),
        )

    # 8) 엔딩 (분기 없는 단일 엔딩, 마지막 단계에 연결)
    e = d["ending"]
    final_step = next(s for s in d["steps"] if s["type"] == "EPILOGUE")["step_id"]
    cur.execute(
        "INSERT INTO story_ending (ending_id, story_id, step_id, ending_name, ending_type, ending_condition, ending_story, display_type, is_default, ending_order) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,'SCRIPT',1,1)",
        (e["ending_id"], STORY_ID, final_step, e["name"], e["type"], e["condition"], e["story"]),
    )
    ids["ending_id"] = e["ending_id"]
    # 규칙이 하나도 없으면 엔딩 배정이 멈추므로, 조건이 빈({}) 규칙으로 항상 이 엔딩을 배정한다.
    cur.execute(
        "INSERT INTO story_ending_rule (rule_id, story_id, target_role_id, target_ending_id, condition_json, priority) VALUES (%s,%s,NULL,%s,'{}',0)",
        (nid(), STORY_ID, e["ending_id"]),
    )
    for i, l in enumerate(e["script"]):
        insert_script_line(cur, "story_ending_script_line", "ending_id", e["ending_id"], i, l, role_ids, npc_ids)
    return ids


def insert_script_line(cur, table, fk, parent_id, i, l, role_ids, npc_ids):
    owner = role_ids[role_key(l["owner"])] if l["owner"] else None
    role_id = npc_id = label = None
    if l["type"] == "PLAYER":
        role_id = role_ids[role_key(l["speaker"])]
        owner = role_id
        label = l["label"]
    elif l["type"] == "NPC":
        npc_id = npc_ids[l["speaker"]]
        label = l["label"]
    cur.execute(
        f"INSERT INTO {table} (line_id, {fk}, line_order, speaker_type, role_id, npc_id, owner_role_id, speaker_label_html, line_html, audio_url) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,NULL)",
        (nid(), parent_id, i, l["type"], role_id, npc_id, owner, label, l["text"]),
    )


def verify(cur, d):
    def one(sql, *a):
        cur.execute(sql, a)
        r = cur.fetchone()
        return list(r.values())[0] if isinstance(r, dict) else r[0]

    n_clues = len(d["clues"])
    n_back = sum(1 for c in d["clues"] if c["back"])
    n_auto = n_clues - n_back
    n_script = sum(len(s["script"]) for s in d["steps"])
    n_ap = sum(len(s["ap"]) for s in d["steps"])
    n_guides = sum(len(r["guidelines"]) for r in d["roles"])
    checks = {
        "roles": (one("SELECT COUNT(*) FROM role WHERE story_id=%s", STORY_ID), 2),
        "role_secret": (one("SELECT COUNT(*) FROM role_secret s JOIN role r ON s.role_id=r.role_id WHERE r.story_id=%s", STORY_ID), 2),
        "steps": (one("SELECT COUNT(*) FROM story_step WHERE story_id=%s", STORY_ID), len(d["steps"])),
        "step_role_ap": (one("SELECT COUNT(*) FROM story_step_role_ap WHERE story_id=%s", STORY_ID), n_ap),
        "guidelines": (one("SELECT COUNT(*) FROM story_step_role_guideline g JOIN story_step s ON g.step_id=s.step_id WHERE s.story_id=%s", STORY_ID), n_guides),
        "step_script_lines": (one("SELECT COUNT(*) FROM story_step_script_line l JOIN story_step s ON l.step_id=s.step_id WHERE s.story_id=%s", STORY_ID), n_script),
        "npcs": (one("SELECT COUNT(*) FROM npc_character WHERE story_id=%s", STORY_ID), 2),
        "groups": (one("SELECT COUNT(*) FROM clue_group WHERE story_id=%s", STORY_ID), 9),
        "clues": (one("SELECT COUNT(*) FROM clue WHERE story_id=%s", STORY_ID), n_clues),
        "variants": (one("SELECT COUNT(*) FROM clue_variant v JOIN clue c ON v.clue_id=c.clue_id WHERE c.story_id=%s", STORY_ID), n_clues),
        "passcode_variants": (one("SELECT COUNT(*) FROM clue_variant v JOIN clue c ON v.clue_id=c.clue_id WHERE c.story_id=%s AND v.passcodes IS NOT NULL", STORY_ID), sum(1 for c in d["clues"] if c["passcode"])),
        "auto_ownership": (one("SELECT COUNT(*) FROM clue_auto_ownership a JOIN clue c ON a.clue_id=c.clue_id WHERE c.story_id=%s", STORY_ID), n_auto),
        "allowed_role": (one("SELECT COUNT(*) FROM clue_acquisition_condition a JOIN clue_variant v ON a.variant_id=v.variant_id JOIN clue c ON v.clue_id=c.clue_id WHERE c.story_id=%s", STORY_ID), n_back),
        "dependencies": (one("SELECT COUNT(*) FROM clue_dependency d JOIN clue c ON d.target_clue_id=c.clue_id WHERE c.story_id=%s", STORY_ID), len(LINKED_BY_DEPENDENCY)),
        "display_rules": (one("SELECT COUNT(*) FROM clue_display_state_rule d JOIN clue c ON d.clue_id=c.clue_id WHERE c.story_id=%s", STORY_ID),
                          n_clues + n_back - len(LINKED_BY_DEPENDENCY)),
        "questions": (one("SELECT COUNT(*) FROM question q JOIN story_step s ON q.step_id=s.step_id WHERE s.story_id=%s", STORY_ID), 6),
        "role_questions": (one("SELECT COUNT(*) FROM question q JOIN story_step s ON q.step_id=s.step_id WHERE s.story_id=%s AND q.role_id IS NOT NULL", STORY_ID), 6),
        "endings": (one("SELECT COUNT(*) FROM story_ending WHERE story_id=%s", STORY_ID), 1),
        "ending_rules": (one("SELECT COUNT(*) FROM story_ending_rule WHERE story_id=%s", STORY_ID), 1),
        "ending_script_lines": (one("SELECT COUNT(*) FROM story_ending_script_line l JOIN story_ending e ON l.ending_id=e.ending_id WHERE e.story_id=%s", STORY_ID), len(d["ending"]["script"])),
        "final_step_outro": (one("SELECT COUNT(*) FROM story_step WHERE story_id=%s AND is_final_step=1 AND outro IS NOT NULL", STORY_ID), 1),
        "rooms_untouched": (one("SELECT COUNT(*) FROM room WHERE story_id=%s", STORY_ID), None),
        "tags_untouched": (one("SELECT COUNT(*) FROM story_tag WHERE story_id=%s", STORY_ID), 3),
    }
    ok = True
    for k, (got, want) in checks.items():
        flag = "" if want is None or got == want else "  <-- 불일치"
        ok = ok and (want is None or got == want)
        print(f"  {k}: {got}" + (f" (기대 {want})" if want is not None else "") + flag)
    return ok


BACKUP_QUERIES = {
    "story": "SELECT * FROM story WHERE story_id=%s",
    "story_tag": "SELECT * FROM story_tag WHERE story_id=%s",
    "story_attribute": "SELECT * FROM story_attribute WHERE story_id=%s",
}


def backup(cur, path):
    data = {}
    for table, sql in BACKUP_QUERIES.items():
        cur.execute(sql, (STORY_ID,))
        data[table] = cur.fetchall()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1, default=str)
    return {k: len(v) for k, v in data.items()}


def summarize(d):
    clues = d["clues"]
    print(f"파싱 OK: 역할 {len(d['roles'])}, 단계 {len(d['steps'])}, 단서 {len(clues)} "
          f"(자동 지급 {sum(c['auto'] for c in clues)}, 보드 뒷면 {sum(c['back'] for c in clues)}, 암호 {sum(bool(c['passcode']) for c in clues)}), "
          f"그룹 {len(d['groups'])}, 질문 {len(d['questions'])}, 엔딩 '{d['ending']['name']}'/{d['ending']['type']} 대본 {len(d['ending']['script'])}줄, "
          f"2단계 대본 {sum(len(s['script']) for s in d['steps'])}줄, 아웃트로 {len(d['outro'])}자, CSS {len(d['info']['css'])}자")
    for s in d["steps"]:
        print(f"  단계 {s['order']} {s['name']} [{s['type']}] 시간 {s['duration']} AP {s['ap']} 대본 {len(s['script'])}줄 설명 {len(s['description'])}자")
    for r in d["roles"]:
        print(f"  역할 {r['character']} ({r['role_name']}) 지침 단계 {sorted(r['guidelines'])} 시트 {len(r['sheet'])}자")
    for c in clues:
        if c["back"]:
            print(f"  보드 clue_{c['num']:02d} {c['name']} 단계{c['stage']} {c['role']} 암호={c['passcode']}")
    for q in d["questions"]:
        print(f"  질문 {q['rubric_id']} {q['role']} 순서{q['order']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rehearse", action="store_true")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    d = parse_all()
    summarize(d)
    if not (args.rehearse or args.apply):
        return

    from infrastructure.database.shared_connection_pool import SharedConnectionPool
    pool = SharedConnectionPool()
    with pool.get_connection() as conn:
        cur = conn.cursor(dictionary=True)
        if args.apply:
            path = os.path.join(BACKUP_DIR, f"db_backup_story_before_register_{datetime.now():%Y%m%d_%H%M%S}.json")
            print("백업 저장:", path, backup(cur, path))
        cur.execute("START TRANSACTION")
        try:
            ids = run(cur, d)
            ok = verify(cur, d)
            if args.apply and ok:
                cur.execute("COMMIT")
                with open(MAP_PATH, "w", encoding="utf-8") as f:
                    json.dump(ids, f, ensure_ascii=False, indent=1)
                print("COMMIT 완료. ID 매핑 저장:", MAP_PATH)
            else:
                cur.execute("ROLLBACK")
                print("ROLLBACK (리허설)" if ok else "ROLLBACK: 검증 실패")
        except Exception:
            cur.execute("ROLLBACK")
            print("오류로 ROLLBACK")
            raise


if __name__ == "__main__":
    main()
