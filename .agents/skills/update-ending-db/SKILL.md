---
name: update-ending-db
description: "엔딩 텍스트 파일(엔딩_개별.txt)의 변경 사항을 MySQL DB의 story_ending 테이블에 부분 덮어쓰기 합니다. EndingID를 기준으로 ending_name과 ending_story 컬럼을 업데이트합니다."
---

# 엔딩 DB 업데이트 (update-ending-db) 가이드

이 스킬은 `EndingID`가 기재된 텍스트 문서(`엔딩_개별.txt`)를 파싱하여, 실제 MySQL 데이터베이스(`murdex` DB)의 `story_ending` 테이블의 `ending_name`과 `ending_story` 컬럼을 덮어쓰는 스크립트를 제공합니다.

## 사용 조건

- 대상 파일 각 엔딩 블록에 `EndingID : [UUID]` 가 기재되어 있어야 합니다.
- 각 블록은 `제목:` 으로 시작하고, `내용:` 줄 이후에 HTML 본문이 위치해야 합니다.
- 업데이트 스크립트는 `murdex-api` 폴더의 환경 변수 및 공통 커넥션 풀을 사용합니다.

## 텍스트 파일 구조

```
<!-- HTML 주석 구분자 (무시됨) -->

제목: 처형되다
EndingID : d38905a2-16dc-4059-85ca-54e0c455af5c
대상 역할: 스컬크러셔
조건: ...
순서: 스컬크러셔-1
내용:
<div class="story-content">
  ...HTML 내용...
</div>
```

## 스크립트 위치 및 사용법

파이썬 스크립트는 이 스킬 폴더 내부의 `scripts/update_ending_db.py` 에 위치해 있습니다.

### 실행 명령어 (터미널)

```bash
# dry-run 모드 (DB 변경 없이 파싱 결과 확인)
python .agents/skills/update-ending-db/scripts/update_ending_db.py "c:\dev\KLIEN\murdex\works\바스타즈 오브 더 유니버스\texts\엔딩_개별.txt" --dry-run

# 실제 DB 업데이트
python .agents/skills/update-ending-db/scripts/update_ending_db.py "c:\dev\KLIEN\murdex\works\바스타즈 오브 더 유니버스\texts\엔딩_개별.txt"
```

## 동작 원리 (파싱 로직)

1. 파일을 읽어 `제목:` 을 기준으로 엔딩 블록을 분리합니다.
2. 각 블록에서 `EndingID`, `제목`, `내용`(HTML)을 추출합니다.
3. `내용:` 줄 이후의 모든 내용을 `ending_story` 값으로 수집합니다.
4. `<!-- ... -->` 형태의 HTML 주석은 자동으로 제거됩니다.
5. `EndingID` 를 기준으로 `story_ending` 테이블의 `ending_name`, `ending_story` 컬럼을 UPDATE합니다.

## 업데이트 대상 컬럼

| 파일 필드 | DB 테이블 | DB 컬럼 |
|---|---|---|
| `제목:` | `story_ending` | `ending_name` |
| `내용:` 이후 HTML | `story_ending` | `ending_story` |
