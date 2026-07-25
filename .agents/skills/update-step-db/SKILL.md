---
name: update-step-db
description: "단계 텍스트 파일(단계_*.txt)의 단계 설명(HTML) 변경 사항을 MySQL DB의 story_step 테이블에 부분 덮어쓰기(UPDATE) 합니다."
---

# 단계 DB 업데이트 (update-step-db) 가이드

이 스킬은 `StepID`가 기재된 단계 텍스트 문서(`단계_*.txt`)를 파싱하여, 실제 MySQL 데이터베이스(`murdex` DB)의 `story_step` 테이블의 `description` 컬럼을 덮어쓰는 스크립트를 제공합니다.

## 사용 조건

- 대상이 되는 `단계_*.txt` 상단에 `StepID : [UUID]` 가 기재되어 있어야 합니다.
- 각 단계 파일 내부에 `7. 단계 설명` 또는 `8. 단계 설명` 아래로 `<div class="story-content">...</div>` HTML 블록이 포함되어 있어야 합니다.
- 업데이트 스크립트는 `murdex-api` 폴더의 환경 변수 및 공통 커넥션 풀을 사용합니다.

## 스크립트 위치 및 사용법

파이썬 스크립트는 이 스킬 폴더 내부의 `scripts/update_step_db.py` 에 위치해 있습니다.

### 실행 명령어 (터미널)

```bash
# 1. 단일 단계 파일 검증 (dry-run 모드)
python .agents/skills/update-step-db/scripts/update_step_db.py "c:\dev\KLIEN\murdex\works\도플로이드\texts\단계_1_시작.txt" --dry-run

# 2. 폴더 내 모든 단계_*.txt 파일 일괄 DB 업데이트
python .agents/skills/update-step-db/scripts/update_step_db.py "c:\dev\KLIEN\murdex\works\도플로이드\texts"
```

## 동작 원리 (파싱 및 업데이트 로직)

1. 지정된 단일 파일 또는 디렉토리 내의 모든 `단계_*.txt` 파일들을 스캔합니다.
2. 각 파일 상단의 `StepID`와 `단계 설명` 하위의 `<div class="story-content">...</div>` HTML 블록을 추출합니다.
3. `StepID`를 매칭 조건으로 하여 MySQL `story_step` 테이블의 `description` 컬럼을 UPDATE 처리합니다.

## 업데이트 대상 컬럼

| 파일 필드 | DB 테이블 | DB 컬럼 |
|---|---|---|
| `StepID :` | `story_step` | `step_id` (WHERE 매칭 키) |
| `단계 설명` 하위 HTML | `story_step` | `description` |
