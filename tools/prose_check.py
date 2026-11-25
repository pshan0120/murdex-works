"""머덱스 작품 문장 검사기.

플레이어가 읽는 문장(역할지, 비밀, 지침, 단서, 대본, 엔딩, 게시판 글)에서
자주 지적받은 버릇을 찾아 줄 번호와 함께 보여 준다. 기계가 어색함을 판단할
수는 없으므로, 여기 걸린 문장은 사람 눈으로 다시 읽고 고칠지 정한다.
규칙은 works/CLAUDE.md "문장 규칙"과 짝을 이룬다.

사용법
  python prose_check.py <파일 또는 폴더> ...       경고만
  python prose_check.py <파일 또는 폴더> --all     참고까지
  python prose_check.py --db <story_id> [--all]    DB 본문 검사(murdex-api/.env 필요)
  python prose_check.py --hook                     Claude Code PostToolUse 훅(stdin JSON)
"""

import html
import json
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

WARN, INFO = "경고", "참고"

# 작업용 메타 줄(플레이어가 보지 않는 것)의 키
INTERNAL_KEYS = {
    "의도", "목적", "근거", "파일명", "코드", "이름", "clueId", "variantId", "이미지",
    "groupId", "GroupID", "유형", "단계", "소모AP", "정렬순서", "중요도", "핵심 단서 여부",
    "교환 가능 여부", "획득 가능 여부", "획득 조건 존재 여부", "획득 조건 내용",
    "시작 표시 상태", "단계 시작시 자동 획득", "관련", "단서 그룹", "화자 타입", "화자",
    "담당 플레이어", "화자 표시 HTML", "설명", "단서 목록", "맞물림", "메모", "참고",
    "이미지 프롬프트", "프롬프트", "역할", "작성자", "게시판", "날짜", "ID", "key",
}
SKIP_PREFIX = ("※", "#", "=", "[", "-----", "//", "* 근거", "* 파일명", "* 이미지 프롬프트")

GO_NOUNS = {"최고", "광고", "신고", "창고", "사고", "경고", "참고", "재고", "원고", "보고", "금고", "공고", "통고", "예고", "선고", "투고", "기고", "회고"}
TRANSLATIONESE = ["에 대해", "을 통해", "를 통해", "에 있어서", "에 있어", "되어지", "에 의해", "로 인해", "으로 인해"]
# 2026-11-25 글다워 보이는 상투어(사람이 실제로 하지 않는 맺음말·격언투). works/CLAUDE.md "장면과 대사"
# 2026-11-25 "share"를 옮긴 "나누다"(정보를 알려 준다는 뜻). "이야기를 나누다", "인사를 나누다"는 괜찮다
SHARE = ["면 나눈다", "정보를 나누", "정보를 나눠", "단서를 나누", "단서를 나눠", "단서 나누기", "비밀을 나누", "알게 된 것을 나누"]
CLICHES = ["비명이 터", "즐거움의 절반", "게임의 일부", "이야기는 이제 시작", "운명의 밤", "모든 것이 바뀌", "진실은 언제나", "침묵이 흐른다", "정적이 흐른다", "공기가 무거", "숨 막히는"]
PARTICLES = sorted(["에서는", "에게서", "으로는", "에서", "에게", "으로", "까지", "부터", "처럼", "보다",
                    "이나", "께서", "은", "는", "이", "가", "을", "를", "에", "의", "도", "로", "와",
                    "과", "만", "랑"], key=len, reverse=True)
STOP = {"그", "이", "저", "것", "수", "때", "더", "안", "못", "잘", "좀", "나", "내", "우리", "당신",
        "그녀", "그는", "그가", "했다", "있다", "없다", "한다", "된다", "하는", "있는", "없는", "그런",
        "이런", "그리고", "하지만", "같은", "함께", "다시", "모두", "사람", "일", "한", "두", "몇",
        "있었다", "없었다", "했고", "있고", "하고", "보니", "말", "얘기", "아무", "어디", "누구", "무엇"}

HANGUL = re.compile(r"[가-힣]")


def strip_tags(s):
    s = re.sub(r"<[^>]+>", "", s)
    return html.unescape(s).strip()


def player_text(line):
    """한 줄에서 플레이어가 읽는 글만 꺼낸다. 없으면 None."""
    s = strip_tags(line)
    if not s:
        return None
    if s.startswith(SKIP_PREFIX):
        return None
    # 타임라인 시각 머리말("18:45 ~ 19:55:", "17:30 무렵:")
    s = re.sub(r"^(점심|저녁|\d{1,2}:\d{2})(\s*~\s*\d{1,2}:\d{2})?(\s*무렵)?\s*[:：]\s*", "", s)
    m = re.match(r"^([^\s:：][^:：]{0,18}?)\s?[:：]\s*(.*)$", s)
    if m:
        key, val = m.group(1).strip(), m.group(2)
        key = key.lstrip("*- ").strip()
        if key in INTERNAL_KEYS:
            return None
        if key in ("대사", "내용", "자막") or len(key) <= 15:
            s = val  # "제목: 본문" 꼴은 본문만 본다
    letters = re.findall(r"[A-Za-z가-힣]", s)
    if not letters:
        return None
    if len(HANGUL.findall(s)) / len(letters) < 0.4:
        return None  # 영어 프롬프트 등
    s = re.sub(r"^[-•·*]\s*", "", s)
    return s or None


def sentences(text):
    parts = re.split(r"(?<=[.?!。])\s+|(?<=[다음함임됨봄옴짐])\.\s*", text)
    return [p.strip() for p in parts if p and len(HANGUL.findall(p)) >= 4]


def stem(tok):
    tok = re.sub(r"[^가-힣]", "", tok)
    for p in PARTICLES:
        if tok.endswith(p) and len(tok) - len(p) >= 2:
            return tok[: -len(p)]
    return tok


ADNOMINAL = re.compile(r"(하|있|없|되|보|오|가|아|주|받|이|던|리|기|우|르|키)는$")
ADVERB_I = {"같이", "많이", "없이", "깊이", "높이", "길이", "일찍이", "굳이", "곧이곧대로", "몹시", "이미", "아이", "사이", "나이", "종이", "자리"}
CONNECTOR = re.compile(r"[가-힣](고|지만|는데|은데|인데|며|면서|다가),\s")


def new_subject(clause):
    """'~고,' 뒤 절의 앞쪽에 새 주어(은/는/도/이/가)가 나오는지."""
    for tok in clause.split()[:7]:
        w = re.sub(r"[^가-힣]", "", tok)
        if len(w) < 2:
            continue
        if w.endswith(("은", "도")) or (w.endswith("는") and not ADNOMINAL.search(w)):
            return True
        if w.endswith(("이", "가")) and w not in ADVERB_I and len(w) >= 3:
            return True
    return False


def check_sentence(s):
    out = []
    go = [m for m in re.finditer(r"([가-힣]+)고,\s", s) if (m.group(1)[-1:] + "고") not in GO_NOUNS and (m.group(1) + "고") not in GO_NOUNS]
    if len(CONNECTOR.findall(s)) >= 2:
        out.append((WARN, "한 문장에 절을 셋 이상 이음('~고,', '~지만,' 등). 서로 다른 사실이면 마침표로 끊기"))
    elif len(go) == 1:
        a, b = s[: go[0].start()], s[go[0].end():]
        if len(HANGUL.findall(a)) >= 6 and len(HANGUL.findall(b)) >= 6:
            seq = re.match(r"\s*(잠시|곧|그 뒤|그러다|이어|다시|얼마|며칠|몇 |그날|이듬해|그해|나머지|그 길로|그때)", b)
            same_pred = a.split()[-1][:2] == b.split()[-1][:2] if a.split() and b.split() else False
            if new_subject(b) and not seq and not same_pred:
                out.append((WARN, "'~고,' 뒤에서 주어가 바뀜. 다른 사실을 붙인 것이면 마침표로 끊기"))
            else:
                out.append((INFO, "'~고,'로 두 사실을 이음. 원인·순서로 이어지는지 확인"))
    if re.search(r"(는|은|인|던)데,", s):
        out.append((WARN, "'~는데,'로 이음. 앞이 뒤의 배경이 아니면 끊기"))
    if re.search(r"데다(가)?,", s):
        out.append((WARN, "'~인 데다,'로 이음. 두 이유가 정말 한 결론을 받치는지 확인"))
    if "아니라" in s:
        out.append((WARN, "'A가 아니라 B' 구문 금지. 사실만 쓰기"))
    if re.search(r"[—–―]", s):
        out.append((WARN, "줄표 금지"))
    if re.search(r"[一-鿿]", s):
        out.append((WARN, "한자 금지"))
    n = len(s)
    if n > 110:
        out.append((WARN, f"너무 긴 문장({n}자). 나눌 곳 찾기"))
    elif n > 85:
        out.append((INFO, f"긴 문장({n}자)"))
    for t in TRANSLATIONESE:
        if t in s:
            out.append((INFO, f"번역투 의심 '{t}'"))
            break
    for t in SHARE:
        if t in s:
            out.append((WARN, f"번역투 '{t}'(share). '말해 준다', '알린다'로 바꾸기"))
            break
    for t in CLICHES:
        if t in s:
            out.append((WARN, f"상투어 '{t}'. 사람이 실제로 하는 말로 바꾸기"))
            break
    seen = {}
    for tok in s.split():
        st = stem(tok)
        if len(st) >= 2 and st not in STOP:
            seen[st] = seen.get(st, 0) + 1
    rep = [w for w, c in seen.items() if c >= 2]
    if rep:
        out.append((INFO, "한 문장 안에서 반복: " + ", ".join(rep[:3])))
    return out


def check_lines(lines, show_info, label):
    results, reported = [], set()
    for no, line in lines:
        t = player_text(line)
        if not t:
            continue
        for s in sentences(t):
            for level, msg in check_sentence(s):
                if level == INFO and not show_info:
                    continue
                key = (msg, s)
                if key in reported:
                    continue
                reported.add(key)
                short = s if len(s) <= 70 else s[:70] + "…"
                results.append(f"{label}:{no} [{level}] {msg}\n    {short}")
    return results


def check_file(path, show_info):
    with open(path, encoding="utf-8", errors="replace") as f:
        lines = list(enumerate(f.read().split("\n"), 1))
    return check_lines(lines, show_info, path)


def iter_paths(args):
    for a in args:
        if os.path.isdir(a):
            for root, _, files in os.walk(a):
                for fn in sorted(files):
                    if fn.endswith(".txt"):
                        yield os.path.join(root, fn)
        elif a.endswith(".txt"):
            yield a


def check_db(story_id, show_info):
    import pymysql
    env = os.path.join(os.path.dirname(__file__), "..", "..", "murdex-api", ".env")
    if os.path.exists(env):
        for l in open(env, encoding="utf-8"):
            if "=" in l and not l.strip().startswith("#"):
                k, v = l.strip().split("=", 1)
                os.environ.setdefault(k, v.strip().strip('"'))
    c = pymysql.connect(host=os.environ["MYSQL_HOST"], port=int(os.environ["MYSQL_PORT"]),
                        user=os.environ["MYSQL_USERNAME"], password=os.environ["MYSQL_PASSWORD"],
                        database=os.environ["MYSQL_DATABASE"], charset="utf8mb4")
    cur = c.cursor()
    queries = [
        ("역할지", "SELECT character_name, description FROM role WHERE story_id=%s"),
        ("비밀", "SELECT CONCAT(r.character_name,'/',s.secret_title), s.secret_content FROM role_secret s JOIN role r ON r.role_id=s.role_id WHERE r.story_id=%s"),
        ("단서", "SELECT v.clue_name, v.clue_content FROM clue_variant v JOIN clue c ON c.clue_id=v.clue_id WHERE c.story_id=%s"),
        ("단계", "SELECT step_name, description FROM story_step WHERE story_id=%s"),
        ("아웃트로", "SELECT step_name, outro FROM story_step WHERE story_id=%s"),
        ("작품 소개", "SELECT title, description FROM story WHERE story_id=%s"),
        ("로비 가이드", "SELECT title, lobby_guide_html FROM story WHERE story_id=%s"),
        ("지침", "SELECT CONCAT(st.step_name,'/',r.character_name), g.description FROM story_step_role_guideline g JOIN story_step st ON st.step_id=g.step_id JOIN role r ON r.role_id=g.role_id WHERE st.story_id=%s"),
        ("대본", "SELECT CONCAT(st.step_name,' #',l.line_order), l.line_html FROM story_step_script_line l JOIN story_step st ON st.step_id=l.step_id WHERE st.story_id=%s"),
        ("엔딩", "SELECT ending_name, ending_story FROM story_ending WHERE story_id=%s"),
        ("엔딩대본", "SELECT CONCAT(e.ending_name,' #',l.line_order), l.line_html FROM story_ending_script_line l JOIN story_ending e ON e.ending_id=l.ending_id WHERE e.story_id=%s"),
    ]
    out = []
    for kind, q in queries:
        cur.execute(q, (story_id,))
        for name, body in cur.fetchall():
            if body:
                out += check_lines(list(enumerate(body.split("\n"), 1)), show_info, f"DB {kind} {name}")
    return out


def run_hook():
    try:
        data = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    except Exception:
        return
    ti = data.get("tool_input") or {}
    path = (ti.get("file_path") or "").replace("\\", "/")
    if "/murdex/works/" not in path or "/texts/" not in path or not path.endswith(".txt"):
        return
    if data.get("tool_name") == "Write":
        chunks = [ti.get("content") or ""]
    else:
        chunks = [ti.get("new_string") or ""] + [e.get("new_string", "") for e in ti.get("edits") or []]
    lines = []
    for ch in chunks:
        lines += [(i, l) for i, l in enumerate(ch.split("\n"), 1)]
    res = check_lines(lines, True, os.path.basename(path) + " (방금 쓴 부분)")
    if not res:
        return
    shown = res[:12]
    more = f"\n…외 {len(res) - 12}건" if len(res) > 12 else ""
    ctx = ("문장 검사(works/tools/prose_check.py)가 방금 고친 글에서 다시 읽을 문장을 찾았다. "
           "works/CLAUDE.md 문장 규칙에 비춰 하나씩 판단하고, 고칠 것은 고친 뒤 넘긴다. "
           "참고 항목은 문제가 없으면 그대로 둬도 된다.\n" + "\n".join(shown) + more)
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": ctx}}, ensure_ascii=False))


def main(argv):
    if "--hook" in argv:
        run_hook()
        return 0
    show_info = "--all" in argv
    args = [a for a in argv if a != "--all"]
    res = []
    if "--db" in args:
        i = args.index("--db")
        res += check_db(args[i + 1], show_info)
        args = args[:i] + args[i + 2:]
    for p in iter_paths(args):
        res += check_file(p, show_info)
    print("\n".join(res) if res else "걸린 문장 없음")
    print(f"\n총 {len(res)}건")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
