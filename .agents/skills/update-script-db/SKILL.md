---
name: update-script-db
description: "단계 텍스트 파일(단계_*.txt)의 대본(9. 대본 관리) 변경 사항을 MySQL DB의 story_step_script_line 테이블에 덮어쓰기(UPDATE) 합니다."
---

# 대본 DB 업데이트 (update-script-db) 가이드

이 스킬은 `StoryID`와 `StepID`가 기재된 단계 텍스트 문서(`단계_*.txt`)의 `9. 대본 관리` 섹션을 파싱하여, 실제 MySQL 데이터베이스(`murdex` DB)의 `story_step_script_line` 테이블의 대본 줄 데이터들을 덮어쓰는 스크립트를 제공합니다.

## 사용 조건

- 대상이 되는 `단계_*.txt` 상단에 `StoryID : [UUID]` 및 `StepID : [UUID]` 가 기재되어 있어야 합니다.
- 각 단계 파일 내부에 `9. 대본 관리` 하위로 `[N] 화자 타입: ...` 형태의 구조화된 대본 블록이 포함되어 있어야 합니다.
- 스크립트는 `murdex-api` 폴더의 환경 변수 및 공통 커넥션 풀을 사용합니다.

## 스크립트 위치 및 사용법

파이썬 스크립트는 이 스킬 폴더 내부의 `scripts/update_script_db.py` 에 위치해 있습니다.

### 실행 명령어 (터미널)

```bash
# 1. 단일 단계 파일 검증 (dry-run 모드)
python .agents/skills/update-script-db/scripts/update_script_db.py "c:\dev\KLIEN\murdex\works\도플로이드\texts\단계_3_A구역_조사.txt" --dry-run

# 2. 단일 단계 파일 실제 DB 업데이트
python .agents/skills/update-script-db/scripts/update_script_db.py "c:\dev\KLIEN\murdex\works\도플로이드\texts\단계_3_A구역_조사.txt"

# 3. 폴더 내 모든 단계_*.txt 파일 일괄 DB 업데이트
python .agents/skills/update-script-db/scripts/update_script_db.py "c:\dev\KLIEN\murdex\works\도플로이드\texts"
```

## 동작 원리 (파싱 및 업데이트 로직)

1. 지정된 단일 파일 또는 디렉토리 내의 `단계_*.txt` 파일들을 스캔합니다.
2. 각 파일 상단의 `StoryID`, `StepID`와 `9. 대본 관리` 하위의 대본 블록들을 파싱합니다.
3. 스토리 DB에서 해당 작품의 플레이어 역할(`role`)과 `npc_character` 목록을 조회하여 `role_id`, `npc_id`를 자동으로 매핑합니다.
4. `NPC` 및 `DIRECTIVE`(지시문) 화자 줄의 담당 플레이어(`owner_role_id`)는 텍스트에 지정된 담당자가 있으면 해당 플레이어로 지정하고, 없는 경우 플레이어 역할들 간 순차적으로 교대(Round-Robin) 배정합니다.
5. `StepID`를 기준으로 해당 단계의 기존 `story_step_script_line` 레코드를 삭제한 뒤, 새 대본 목록을 일괄 삽입(INSERT)합니다.
