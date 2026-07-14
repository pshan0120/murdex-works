---
name: update-clue-db
description: "단서 텍스트 파일(단서.txt)의 변경 사항을 MySQL DB에 부분 덮어쓰기 합니다."
---

# 단서 DB 업데이트 (update-clue-db) 가이드

이 스킬은 `StoryID`와 `clue_id`, `variant_id` 가 기재된 텍스트 문서(`단서.txt`)를 파싱하여, 실제 MySQL 데이터베이스(`murdex` DB)의 `clue_variant` 테이블의 특정 필드를 덮어쓰는 스크립트를 제공합니다.

## 사용 조건
- 대상이 되는 `단서.txt` 상단에 `StoryID : [UUID]` 가 기재되어 있어야 합니다.
- 각 단서 항목 내부에 `clue_id : [UUID]` 및 `variant_id : [UUID]` 가 기재되어 있어야 합니다.
- 업데이트 스크립트는 `murdex-api` 폴더의 환경 변수 및 공통 커넥션 풀을 사용합니다.

## 스크립트 위치 및 사용법

파이썬 스크립트는 이 스킬 폴더 내부의 `scripts/update_db.py` 에 위치해 있습니다.

### 실행 명령어 (터미널)
```bash
# 워크스페이스 루트에서 실행 시
python .agents/skills/update-clue-db/scripts/update_db.py "c:\dev\KLIEN\murdex\works\누룩꽃 필 무렵\texts\단서.txt"
```

## 동작 원리 (파싱 로직)
- 스크립트는 텍스트 파일을 읽고 `이름 :` 으로 시작하는 블록 단위로 분리합니다.
- 각 블록 내에 있는 `variant_id`를 식별합니다.
- 스크립트 코드 내부의 로직을 통해 `HTML :` 또는 다른 대상 필드 하위 내용을 추출합니다.
- 추출한 `HTML` 내용은 `clue_variant` 테이블의 `clue_content` 컬럼으로 UPDATE 처리됩니다.
