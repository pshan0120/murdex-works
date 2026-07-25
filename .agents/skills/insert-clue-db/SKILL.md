---
name: insert-clue-db
description: 단서 텍스트 파일(단서.txt)의 내용을 MySQL DB에 신규 삽입(INSERT)하고, 생성된 UUID를 단서.txt 파일에 채워 넣습니다.
---

# insert-clue-db 스킬 가이드

`단서.txt` 파일에 기록된 단서 정보를 읽어, MySQL DB(`clue`, `clue_variant`)에 신규 데이터를 등록합니다.
이후 DB에 할당할 식별용 UUID(`clue_id`, `variant_id`)를 텍스트 파일 내에 빈 칸으로 남아 있던 필드에 자동으로 덮어씁니다.

## 사용법

단서 텍스트 파일의 경로를 인자로 넘겨 스크립트를 실행합니다.

```bash
python c:\dev\KLIEN\murdex\works\.agents\skills\insert-clue-db\scripts\insert_db.py "c:\dev\KLIEN\murdex\works\도플로이드\texts\단서.txt"
```

## 기능 상세

1. **파일 읽기 및 ID 부여**:
   `단서.txt`를 읽고, `clue_id : ` 나 `variant_id : ` 부분이 비어있는 단서 블록들에 대해 새로운 UUIDv4를 생성해 텍스트 파일에 즉시 덮어씁니다.
2. **단서 그룹 매핑**:
   같은 디렉토리 내의 `단서_그룹.txt` 파일을 읽어 각 그룹의 고유 식별자(`group_id`)를 조회합니다.
3. **데이터베이스 삽입**:
   `murdex-api`의 공유 커넥션 풀을 활용하여 `clue` 와 `clue_variant` 테이블에 데이터를 `INSERT` 합니다.
4. **변형(Variant) 단서**:
   이름에 `(변형)`이 포함된 단서는 자동 삽입에서 제외됩니다. (사용자가 별도로 수동 기입/처리)

## 테스트 모드

실제로 DB에 넣지 않고 동작을 확인하고 싶다면 `--dry-run` 플래그를 추가합니다.

```bash
python c:\dev\KLIEN\murdex\works\.agents\skills\insert-clue-db\scripts\insert_db.py "c:\dev\KLIEN\murdex\works\도플로이드\texts\단서.txt" --dry-run
```
