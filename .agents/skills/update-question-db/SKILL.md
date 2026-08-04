---
name: update-question-db
description: "질문 텍스트 파일(질문_개별.txt, 질문_공통.txt)의 변경 사항을 MySQL DB의 question 및 question_option 테이블에 부분 덮어쓰기 합니다. QuestionID를 기준으로 질문 제목(title) 및 선택지 목록(option_text)을 업데이트합니다."
---

# 질문 DB 업데이트 (update-question-db) 가이드

이 스킬은 `QuestionID`가 기재된 질문 텍스트 문서(`질문_개별.txt`, `질문_공통.txt` 등)를 파싱하여, 실제 MySQL 데이터베이스(`murdex` DB)의 `question` 테이블과 `question_option` 테이블을 덮어쓰는 스크립트를 제공합니다.

## 사용 조건

- 각 질문 블록 상단에 `QuestionID : [UUID]` 가 기재되어 있어야 합니다.
- `[질문]` 태그 이하의 `<div class="story-content">` 블록이 질문 본문(`question.title`)으로 파싱됩니다.
- `[선택지]` 태그 이하의 연속된 `<div class="story-content">` 블록들이 선택지 목록(`question_option.option_text`)으로 순서대로 파싱됩니다.
- 업데이트 스크립트는 `murdex-api` 폴더의 환경 변수 및 공통 커넥션 풀을 사용합니다.

## 텍스트 파일 표준 구조

```html
QuestionID : d681c581-9a33-48d6-99a7-10600bc4910e
[질문]
<div class="story-content">
  <div class="section-title">1. 처형 대상 지목</div>
  <p>
    처형할 대상을 선택해 주세요.
  </p>
</div>

[선택지]
<div class="story-content">
  스컬크러셔
</div>

<div class="story-content">
  말리스
</div>

<div class="story-content">
  기권
</div>
```

## 스크립트 위치 및 사용법

파이썬 스크립트는 이 스킬 폴더 내부의 `scripts/update_question_db.py` 에 위치해 있습니다.

### 실행 명령어 (터미널)

```bash
# dry-run 모드 (DB 변경 없이 파싱 결과 확인)
python .agents/skills/update-question-db/scripts/update_question_db.py "c:\dev\KLIEN\murdex\works\바스타즈 오브 더 유니버스\texts\질문_개별.txt" --dry-run

# 실제 DB 업데이트
python .agents/skills/update-question-db/scripts/update_question_db.py "c:\dev\KLIEN\murdex\works\바스타즈 오브 더 유니버스\texts\질문_개별.txt"

# DB의 QuestionID 및 [질문], [선택지] 태그를 기존 문서에 자동 주입 및 변환
python .agents/skills/update-question-db/scripts/update_question_db.py "c:\dev\KLIEN\murdex\works\바스타즈 오브 더 유니버스\texts\질문_개별.txt" --inject
```

## 동작 원리 (파싱 및 업데이트 로직)

1. 문서를 `QuestionID : [UUID]` 패턴으로 구분하여 각 질문 블록을 추출합니다.
2. `[질문]` 구문 바로 아래의 첫 번째 `<div class="story-content">...</div>` 블록을 추출하여 `question` 테이블의 `title` 컬럼에 UPDATE합니다.
3. `[선택지]` 구문 이하의 모든 `<div class="story-content">...</div>` 블록들을 추출하여 순서(`option_order` 1, 2, 3...)에 맞게 `question_option` 테이블의 `option_text` 컬럼에 UPDATE합니다.
