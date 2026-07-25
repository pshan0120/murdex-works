---
name: decorate-txt-html
description: 텍스트 파일(엔딩.txt, 단서.txt, 단계_*.txt 등) 내 HTML 영역을 스캔하여, 캐릭터명(.character-*)과 주요 장소/단서/키워드(.emphasis)에 지정된 CSS span 태그 장식을 자동 적용합니다.
---

# decorate-txt-html 스킬 가이드

텍스트 파일 내 HTML 스토리 콘텐츠 영역(`<div class="story-content">`, `HTML :` 등)을 분석하여, 누락된 캐릭터 고유 색상 태그(`<span class="character-veyla">`, `<span class="character-marcus">` 등) 및 주요 키워드/장소 강조 태그(`<span class="emphasis">`)를 자동으로 탐색하여 태깅합니다.

## 작동 원리

1. **자동 키워드 수집**:
   - 대상 파일이 포함된 작품 폴더 내의 텍스트 파일(`단서_그룹.txt`, `역할_*.txt` 등) 및 `.css` 파일을 참조합니다.
   - 캐릭터명(`베일라`, `마커스`, `클레이`, `알렉스` 등)은 해당 역할 고유 클래스(`.character-veyla`, `.character-marcus`, `.character-clay`, `.character-alex`)로 맵핑합니다.
   - 주요 장소 및 구역명(`정문 로비`, `소장실`, `지하 배양실`, `도플로이드` 등)은 `.emphasis` 클래스로 맵핑합니다.

2. **중복 태깅 방지**:
   - 이미 `<span class="...">` 내부에 감싸져 있거나 HTML 태그 속성 문자열인 키워드는 건너뜁니다.
   - 문장 내에서 긴 구문(예: `닥터 클레이`)을 우선 단어(예: `클레이`)보다 먼저 매칭하여 안전하게 덮어씁니다.

## 사용법

단일 파일 또는 텍스트 디렉토리 경로를 인자로 전달하여 실행합니다.

```bash
python "c:\dev\KLIEN\murdex\works\.agents\skills\decorate-txt-html\scripts\decorate_html.py" "c:\dev\KLIEN\murdex\works\도플로이드\texts\엔딩.txt"
```

### 테스트 (Dry-Run)
실제 파일 수정 없이 감지 및 치환 대상 개수만 확인하려면 `--dry-run` 옵션을 붙입니다.

```bash
python "c:\dev\KLIEN\murdex\works\.agents\skills\decorate-txt-html\scripts\decorate_html.py" "c:\dev\KLIEN\murdex\works\도플로이드\texts\엔딩.txt" --dry-run
```
