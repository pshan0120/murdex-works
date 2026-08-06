---
name: upload-script-audio
description: "합쳐진 대본 음성 mp3(concat-voice-wav 결과물)를 Cloudinary에 업로드하고(크리에이터 화면 BGM 업로드와 동일한 API 사용), 받은 URL을 단계_*.txt의 '대본 낭독' <audio> 태그 src에 자동으로 채워 넣습니다."
---

# 대본 음성 업로드·삽입 스킬 (upload-script-audio)

단계별로 합쳐진 mp3 파일을 murdex 저장소(Cloudinary)에 올리고, 그 URL을 해당 단계 텍스트 파일의 `<audio><source src="...">`에 바로 써 넣습니다. 사용하는 업로드 API는 크리에이터 화면의 "룸 로비 BGM"/"단계 BGM" 업로드 버튼과 **완전히 동일한 엔드포인트**(`POST /api/storage/upload/audio`)입니다.

**주의: 이 스킬은 DB에 아무것도 쓰지 않습니다.** 대본음성 URL은 별도 DB 컬럼이 아니라 단계 설명 HTML 안 `<audio>` 태그로만 존재하는 값이라서, txt 파일을 고치는 것만으로 충분합니다. (반대로 이 txt의 변경 내용을 실제 서비스 DB에 반영하려면 별도로 `update-step-db` 스킬을 실행해야 합니다 — 아래 "다음 단계" 참고.)

또한 **로컬 개발 서버(`http://localhost:8601`)에서만 동작**합니다. 업로드에 필요한 로그인 토큰을 murdex-api의 시크릿 키로 직접 발급하는 방식이라, 로컬 개발 DB/서버가 아닌 곳에는 절대 쓰면 안 됩니다.

## 사전 준비

1. murdex-api 로컬 개발 서버가 `http://localhost:8601`에서 실행 중이어야 합니다.
2. `pip install requests` (없으면 먼저 설치).
3. 대상 단계 파일 안에 빈 `<source src="" type="audio/mpeg" />` 태그가 정확히 하나 있어야 합니다 (`<audio>` 태그의 정확한 위치나 다른 속성은 상관없이, 이 `source` 태그 하나만 찾아서 src만 바꿔치기합니다). 0개면 태그가 없다는 뜻이고, 2개 이상이면 어느 걸 바꿀지 애매하다는 뜻으로 에러를 냅니다.

## 사용 방법 (터미널 명령어)

```bash
python .agents/skills/upload-script-audio/scripts/upload_script_audio.py "c:\dev\KLIEN\murdex\works\도플로이드\audios\voice\단계_5_C구역_조사.mp3" "c:\dev\KLIEN\murdex\works\도플로이드\texts\단계_5_C구역_조사.txt"
```

성공하면 콘솔에 최종 Cloudinary URL이 출력되고, 지정한 단계 파일이 그 URL로 바로 수정됩니다.

## 동작 원리

1. 단계 파일 상단의 `StoryID`로 실제 작품을 찾아 작가(creator)의 member_id를 얻습니다.
2. 그 member_id로 로컬 전용 로그인 토큰을 발급합니다 (실서버 계정이 아니라, 로컬 DB에 이미 존재하는 그 작가 본인 계정으로 "로그인한 것처럼" 만드는 것 — 실제 비밀번호 없이도 로컬 개발 환경에서만 가능한 지름길입니다).
3. 그 토큰으로 `POST /api/storage/upload/audio`에 mp3를 업로드합니다 (BGM 업로드와 동일 API).
4. 응답으로 받은 URL을 단계 파일의 `<audio><source src="">`에 정규식으로 찾아 바꿔치기합니다.

## 다음 단계 (관련 스킬)

- 이 스킬이 고친 txt 파일 내용을 실제 서비스 DB(`story_step.description`)에도 반영하려면, 기존 스킬 `.agents/skills/update-step-db/scripts/update_step_db.py`를 이어서 실행하세요. 이 스킬은 txt 파일만 고치고 DB는 건드리지 않습니다.
