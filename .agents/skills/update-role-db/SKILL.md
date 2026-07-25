---
name: update-role-db
description: "역할 텍스트 파일(역할_*.txt)의 공개 정보 및 상세 정보(역할 시트) HTML 변경 사항을 MySQL DB에 부분 덮어쓰기 합니다."
---

# 역할 정보 DB 업데이트 (update-role-db) 가이드

이 스킬은 `RoleID`가 기재된 역할 텍스트 문서(`역할_*.txt`)를 파싱하여, 실제 MySQL 데이터베이스(`murdex` DB)의 `role` 테이블의 `public_info` 및 `description` 필드를 덮어쓰는 스크립트를 제공합니다.

## 사용 조건
- 대상이 되는 `역할_*.txt` 상단에 `RoleID : [UUID]` 가 기재되어 있어야 합니다.
- 파일 내부에 `6. 공개 정보`와 `7. 역할 시트` 섹션 하위에 `<div class="story-content">...</div>` 블록이 존재해야 합니다.
- 업데이트 스크립트는 `murdex-api` 폴더의 환경 변수 및 공통 커넥션 풀을 사용합니다.

## 스크립트 위치 및 사용법

파이썬 스크립트는 이 스킬 폴더 내부의 `scripts/update_role_db.py` 에 위치해 있습니다.

### 실행 명령어 (터미널)
```bash
# 특정 파일 하나만 업데이트할 경우
python .agents/skills/update-role-db/scripts/update_role_db.py "c:\dev\KLIEN\murdex\works\도플로이드\texts\역할_1_베일라.txt"

# 텍스트 폴더 전체를 지정하여 일괄 업데이트할 경우
python .agents/skills/update-role-db/scripts/update_role_db.py "c:\dev\KLIEN\murdex\works\도플로이드\texts"
```

## 동작 원리 (파싱 로직)
- 스크립트는 파일명에서 `역할_*.txt` 패턴을 갖는 파일만 자동으로 필터링합니다.
- 파일 내의 `RoleID`를 파싱하여 업데이트할 고유 키로 식별합니다.
- `6. 공개 정보` 이후 등장하는 첫 `<div class="story-content">` 블록을 파싱하여 `public_info` 컬럼에 UPDATE 합니다.
- `7. 역할 시트` 이후 등장하는 첫 `<div class="story-content">` 블록을 파싱하여 `description` 컬럼에 UPDATE 합니다.
- 건너뛰고 싶거나 찾지 못한 섹션은 무시하고 추출 가능한 정보만 덮어씁니다.
