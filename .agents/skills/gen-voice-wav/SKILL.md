---
name: gen-voice-wav
description: "단계_*.txt의 '대본 낭독'/'마지막 대화' 섹션에 있는 지시문과 대사를 화자별로 로컬 GPT-SoVITS TTS API(http://localhost:9872/)에 보내 개별 WAV 파일로 생성합니다. 단계 전체를 한 번에 만들 수도, 특정 한 줄만 다시 만들 수도 있습니다."
---

# 대본 음성(WAV) 생성 스킬 (gen-voice-wav)

단계 파일의 대본(지시문 + 대사)을 문서에 등장하는 순서 그대로 훑어서, 화자에 맞는 목소리로 로컬 GPT-SoVITS(Gradio API)에 보내 WAV 파일들을 생성합니다. 지시문은 항상 "나레이터" 목소리로 읽습니다.

## 사전 준비

1. GPT-SoVITS WebUI가 `http://localhost:9872/`에서 실행 중이어야 합니다 (Gradio API 활성 상태).
2. 작품 폴더 아래 `audios/voice/voices.json`에 화자별 참고 음성 설정이 있어야 합니다 (없으면 아래 "voices.json 만들기" 참고).
3. `pip install gradio_client beautifulsoup4` (둘 다 없으면 먼저 설치).

## 사용 방법 (터미널 명령어)

### 1. 단계 하나의 대본 전체를 WAV로 생성
```bash
python .agents/skills/gen-voice-wav/scripts/gen_voice_wav.py "c:\dev\KLIEN\murdex\works\도플로이드\texts\단계_5_C구역_조사.txt"
```
`works/도플로이드/audios/voice/단계_5_C구역_조사_1.wav`, `_2.wav`, ... 순서대로 생성됩니다.

### 2. 특정 한 줄만 다시 생성 (특정 wav만 이상하게 들릴 때)
```bash
python .agents/skills/gen-voice-wav/scripts/gen_voice_wav.py "c:\dev\KLIEN\murdex\works\도플로이드\texts\단계_5_C구역_조사.txt" --line 14
```
해당 번호의 wav 파일만 새로 만들어 덮어씁니다. 몇 번이 몇 번째 줄인지 헷갈리면 `--dry-run`으로 먼저 목록을 확인하세요.

### 3. 특정 줄부터 끝까지 이어서 생성 (앞부분은 이미 수작업/이전 실행으로 만들어둔 경우)
```bash
python .agents/skills/gen-voice-wav/scripts/gen_voice_wav.py "c:\dev\KLIEN\murdex\works\도플로이드\texts\단계_4_B구역_조사.txt" --from 6
```

### 3-1. 특정 범위(N~M번)만 재생성 (그 구간만 순서가 꼬였거나 이상하게 나온 경우)
```bash
python .agents/skills/gen-voice-wav/scripts/gen_voice_wav.py "c:\dev\KLIEN\murdex\works\도플로이드\texts\단계_4_B구역_조사.txt" --from 1 --to 5
```

### 4. 실제 생성 없이 목록만 미리 보기
```bash
python .agents/skills/gen-voice-wav/scripts/gen_voice_wav.py "c:\dev\KLIEN\murdex\works\도플로이드\texts\단계_5_C구역_조사.txt" --dry-run
```
각 줄 번호, 화자, 적용될 speed, 텍스트 앞부분을 출력합니다. 줄 번호가 예상과 다르면(예: 지시문 하나가 실수로 두 번 잡히는 등) 여기서 먼저 확인하세요.

## 그 다음 단계 (관련 스킬)

- 생성된 WAV들을 하나의 mp3로 합치려면 기존 스킬 `.agents/skills/concat-voice-wav/scripts/concat_voice_wav.py`를 사용하세요 (와일드카드로 `단계_5_C구역_조사_*.wav` 지정).
- mp3를 Cloudinary에 올리고 단계 파일의 `<audio>` 태그 `src`에 채워 넣으려면 `.agents/skills/upload-script-audio`를 사용하세요.

## voices.json 만들기 (새 작품/새 목소리를 추가할 때)

작품마다 `works/<작품명>/audios/voice/voices.json`이 있어야 합니다. 구조:

```json
{
  "gpt_model": "GPT_SoVITS/pretrained_models/...",
  "sovits_model": "GPT_SoVITS/pretrained_models/...",
  "language": "한국어",
  "voices": {
    "캐릭터이름": {
      "ref_audio": "actor/캐릭터이름 (mp3cut.net).mp3",
      "ref_text": "참고 음성 파일의 정확한 대사 원문",
      "speed": 0.95
    },
    "파인튜닝한캐릭터": {
      "ref_audio": "actor/파인튜닝한캐릭터 (mp3cut.net).mp3",
      "ref_text": "참고 음성 파일의 정확한 대사 원문",
      "speed": 0.9,
      "gpt_model": "GPT_weights/파인튜닝한캐릭터-e15.ckpt",
      "sovits_model": "SoVITS_weights/파인튜닝한캐릭터_e8_s...pth"
    }
  },
  "speed_overrides": {
    "단계_5_C구역_조사": { "캐릭터이름": 1.0 }
  }
}
```

- `voices`의 key는 대본 안 `<span class="character-XXX">이름</span>`의 **이름 텍스트와 정확히 일치**해야 합니다 (지시문은 항상 `나레이터`로 자동 처리).
- `gpt_model`/`sovits_model`은 GPT-SoVITS WebUI에서 현재 선택 중인 모델 경로를 그대로 적으면 됩니다 (WebUI 화면의 드롭다운에 표시된 전체 경로 문자열). **최상위 `gpt_model`/`sovits_model`은 모든 목소리가 공유하는 기본값**이고, 특정 캐릭터를 따로 파인튜닝했다면 그 캐릭터 항목 안에 같은 이름의 키를 추가하면 그 목소리에만 적용됩니다(예시의 "파인튜닝한캐릭터"). 스크립트가 줄마다 필요한 모델이 이전과 다르면 자동으로 전환하므로 신경 쓸 필요 없습니다.
- `ref_audio`는 voices.json이 있는 폴더(`audios/voice/`) 기준 상대경로입니다. 3~10초 이내 클립이어야 합니다(GPT-SoVITS 제약, 파인튜닝한 모델이라도 추론 시 참고 음성 자체는 여전히 필요합니다).
- `speed_overrides`는 선택 사항입니다. 같은 캐릭터라도 특정 단계부터는 다른 speed를 쓰고 싶을 때(예: 정체가 의심되기 시작하면서 말투가 미묘하게 달라지는 연출) 단계 파일명(확장자 제외) 기준으로 덮어씁니다.

## 동작 원리

1. 단계 파일에서 `<div class="story-content">...` HTML 블록을 찾습니다.
2. "1. 대본 낭독" 또는 "1. 마지막 대화" 섹션 제목부터 다음 섹션 제목 전까지, `script-direction`(지시문)과 `script-line`(대사)을 문서 순서 그대로 추출합니다. 이 순서가 곧 출력 파일의 번호(`_1`, `_2`, ...)입니다.
3. 대사는 큰따옴표 안 텍스트만 추출하고, 나머지 HTML 태그는 모두 제거합니다. 대사 중간에 섞인 `(마주 앉는 순간, 흠칫 놀라며)` 같은 연기 지시 괄호도 읽지 않도록 제거합니다.
4. 화자별 참고 음성/텍스트/speed를 voices.json에서 찾아 GPT-SoVITS의 `/get_tts_wav` API를 호출합니다.
5. 결과 wav를 `<단계파일명>_<번호>.wav`로 `audios/voice/` 폴더에 저장합니다.
