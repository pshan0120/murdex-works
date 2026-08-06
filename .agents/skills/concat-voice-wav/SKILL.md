---
name: concat-voice-wav
description: "여러 개의 대사 WAV 음성 파일들을 순서대로 지정된 무음 간격(기본 0.6초)을 두어 하나의 MP3 파일로 합성합니다."
---

# 대사 음성 파일 병합 스킬 (concat-voice-wav)

이 스킬은 개별 대사의 WAV 음성 파일들(`단계_2_대면_1.wav`, `단계_2_대면_2.wav` 등)을 자연스러운 숫자 순서로 정렬하고, 대사 사이사이에 지정된 쉼(무음) 간격을 삽입하여 하나의 MP3 파일로 병합합니다.

## 스크립트 위치

`concat_voice_wav.py` 파이썬 스크립트는 이 스킬 폴더 내부에 위치해 있습니다.
- 파일 경로: `.agents/skills/concat-voice-wav/scripts/concat_voice_wav.py`

## 사용 방법 (터미널 명령어)

### 1. 와일드카드 패턴으로 WAV 파일 일괄 병합
```bash
python .agents/skills/concat-voice-wav/scripts/concat_voice_wav.py "c:\dev\KLIEN\murdex\works\도플로이드\audios\voice\단계_2_대면_*.wav" -o "c:\dev\KLIEN\murdex\works\도플로이드\audios\voice\단계_2_대면.mp3"
```

### 2. 개별 파일 목록 지정 병합
```bash
python .agents/skills/concat-voice-wav/scripts/concat_voice_wav.py "path/to/file_1.wav" "path/to/file_2.wav" -o "path/to/output.mp3"
```

### 3. 대사 사이 간격(초) 조절 (기본값: 0.6초)
```bash
python .agents/skills/concat-voice-wav/scripts/concat_voice_wav.py "c:\dev\KLIEN\murdex\works\도플로이드\audios\voice\단계_2_대면_*.wav" -p 0.8 -o "c:\dev\KLIEN\murdex\works\도플로이드\audios\voice\단계_2_대면.mp3"
```

## 옵션 설명
- `-o`, `--output`: 출력될 MP3 파일 경로 (미지정 시 첫 번째 파일 명칭 기반으로 자동 지정)
- `-p`, `--pause-sec`: 대사 간 무음 간격 시간 (초 단위, 기본값: `0.6`초)
- `--bitrate`: MP3 품질 비트레이트 (기본값: `192k`)
