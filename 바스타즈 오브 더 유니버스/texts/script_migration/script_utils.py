# -*- coding: utf-8 -*-
"""바스타즈 대본 전환 공용 유틸리티.

원본 .txt의 <div class="script-line">/<div class="script-direction">/<p> 마크업을
story_step_script_line / story_ending_script_line 테이블용 줄 배열로 변환할 때
step/ending 변환 스크립트가 공통으로 쓰는 함수 모음.
"""
import re, json

ROLE_MAP_PATH = r"C:\dev\KLIEN\murdex\works\바스타즈 오브 더 유니버스\texts\_role_id_map.json"

QUOTE_TOKENS = ['&quot;', '"']


def load_role_map():
    with open(ROLE_MAP_PATH, encoding="utf-8") as f:
        roles = json.load(f)
    return {r["character_name"]: r["role_id"] for r in roles}, [r["role_id"] for r in roles]


def _find_direction_span_end(c):
    """c는 '<span class="script-direction">'로 시작한다고 가정. 그 안에 중첩된
    <span>(예: character-bastards 강조)이 있어도 깨지지 않도록, 태그 깊이를 세어
    실제로 짝이 맞는 닫는 </span> 바로 뒤 위치를 반환한다."""
    open_tag = '<span class="script-direction">'
    pos = len(open_tag)
    depth = 1
    while depth > 0:
        next_open = c.find('<span', pos)
        next_close = c.find('</span>', pos)
        if next_close == -1:
            return len(c)  # 형식이 어긋난 경우 방어적으로 끝까지
        if next_open != -1 and next_open < next_close:
            depth += 1
            pos = next_open + len('<span')
        else:
            depth -= 1
            pos = next_close + len('</span>')
    return pos


def strip_wrapping_quotes(content):
    """대사 앞뒤를 감싼 따옴표(" 또는 &quot;)를 제거한다.
    도플로이드 실제 데이터를 확인한 결과 lineHtml에는 따옴표를 넣지 않는 게 관례
    (ScriptReadingArea가 말풍선 스타일로 대사임을 표시하므로 따옴표는 중복 표기가 됨).
    앞에 <span class="script-direction">...</span> 지문이 붙어 있는 경우 그 뒤의
    따옴표만 벗기고 지문 자체는 그대로 둔다. 지문 안에 <span class="character-x">처럼
    중첩된 span이 있어도 실제 짝이 맞는 닫는 태그를 찾아 처리한다.
    """
    c = content.strip()
    prefix = ""
    if c.startswith('<span class="script-direction">'):
        end = _find_direction_span_end(c)
        prefix = c[:end]
        rest = c[end:].lstrip()
    else:
        rest = c
    for tok in QUOTE_TOKENS:
        if rest.startswith(tok):
            rest = rest[len(tok):]
            break
    rest = rest.rstrip()
    for tok in QUOTE_TOKENS:
        if rest.endswith(tok):
            rest = rest[:-len(tok)]
            break
    rest = rest.strip()
    return f"{prefix} {rest}".strip() if prefix else rest


def resolve_role(label_html, name_to_role_id):
    """화자 표시 HTML에서 역할을 찾는다. "다크 시리어스(엘드리치)"처럼 변형된
    라벨은 role_id만 원래 캐릭터로 매핑하고 speakerLabelHtml은 원문 그대로 보존한다."""
    for slug, name in re.findall(r'<span class="character-(\w[\w-]*)">([^<]+)</span>', label_html):
        if name in name_to_role_id:
            return name_to_role_id[name], label_html
    plain = re.sub(r'<[^>]+>', '', label_html)
    for name, rid in name_to_role_id.items():
        if name in plain:
            return rid, label_html
    return None, label_html


def extract_balanced_div(text, start_pos):
    """text[start_pos:]가 여는 '<div' 태그로 시작한다고 가정하고, 태그 깊이를 세어
    그 div와 실제로 짝이 맞는 닫는 '</div>' 바로 뒤 위치를 반환한다.
    (엔딩_메타.txt(구 엔딩_공통.txt)/단계 파일의 script-container처럼 내부에 다른 <div>가 중첩된
    블록의 경계를 정규식 non-greedy만으로는 정확히 못 찾아서 필요.)"""
    assert text[start_pos:start_pos + 4] == '<div'
    pos = text.index('>', start_pos) + 1
    depth = 1
    while depth > 0:
        next_open = text.find('<div', pos)
        next_close = text.find('</div>', pos)
        if next_close == -1:
            return len(text)
        if next_open != -1 and next_open < next_close:
            depth += 1
            pos = next_open + 4
        else:
            depth -= 1
            pos = next_close + len('</div>')
    return pos


class RoundRobin:
    """등장 순서대로 만난 역할들 사이에서 지문/서술 줄 소유권을 고르게 순환 배정.

    다만 실제로 대사가 있는 인물이 사실상 1명뿐인 스크립트(예: 막간 I — 스컬크러셔 혼자만 대사함)에서는
    그 한 명 사이에서만 "순환"해봐야 결국 전부 그 사람에게 몰린다. 이런 경우 fallback_pool(전체 배역
    목록)이 주어져 있으면, 그 화자를 제외한 나머지 인물들 사이에서 지문 담당을 배정해 최소한
    지문 줄만큼은 다른 플레이어들도 진행 버튼을 조작할 기회를 갖게 한다."""

    def __init__(self, fallback_pool=None):
        self.present_roles = []
        self.fallback_pool = fallback_pool or []
        self._idx = 0

    def note_speaker(self, role_id):
        if role_id and role_id not in self.present_roles:
            self.present_roles.append(role_id)

    def _pool(self):
        if len(self.present_roles) <= 1 and self.fallback_pool:
            exclude = set(self.present_roles)
            others = [r for r in self.fallback_pool if r not in exclude]
            if others:
                return others
        return self.present_roles

    def next_owner(self):
        pool = self._pool()
        if not pool:
            return None
        rid = pool[self._idx % len(pool)]
        self._idx += 1
        return rid
