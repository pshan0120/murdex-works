---
name: convert-suno-url
description: "Suno AI 공유 URL(https://suno.com/s/... 또는 https://suno.com/song/...)을 감지하여 직접 스트리밍 재생이 가능한 CDN MP3 URL(https://cdn1.suno.ai/<UUID>.mp3)로 자동 변환합니다."
---

# Suno URL 자동 변환 스킬 (convert-suno-url)

이 스킬은 Suno AI 웹사이트의 공유 URL(`https://suno.com/s/...` 또는 `https://suno.com/song/...`)에서 고유 `Song UUID`를 자동으로 추적·추출하여, 오디오 플레이어에서 직접 재생 가능한 **CDN MP3 스트리밍 URL**(`https://cdn1.suno.ai/<UUID>.mp3`)로 치환합니다.

## 스크립트 위치

`convert_suno_url.py` 파이썬 스크립트는 이 스킬 폴더 내부에 위치해 있습니다.
- 파일 경로: `.agents/skills/convert-suno-url/scripts/convert_suno_url.py`

## 사용 방법 (터미널 명령어)

### 1. 단일 Suno URL 변환 (문자열 입력)
```bash
python .agents/skills/convert-suno-url/scripts/convert_suno_url.py "https://suno.com/s/GDnbiwowL3IslVa0"
```
* **출력 결과**: `Direct CDN MP3 URL: https://cdn1.suno.ai/6843d874-c15a-4bd2-8fb5-71b2a6f72078.mp3`

---

### 2. 단일 텍스트 파일 변환 (`단계_*.txt` 등)
```bash
python .agents/skills/convert-suno-url/scripts/convert_suno_url.py "c:\dev\KLIEN\murdex\works\바스타즈 오브 더 유니버스\texts\단계_1_서막.txt"
```
* 파일 내에 존재하는 `https://suno.com/s/...` 또는 `https://suno.com/song/...` 링크가 자동으로 `https://cdn1.suno.ai/<UUID>.mp3` 로 치환됩니다.

---

### 3. 미리보기 (Dry-Run 모드)
```bash
python .agents/skills/convert-suno-url/scripts/convert_suno_url.py "c:\dev\KLIEN\murdex\works\바스타즈 오브 더 유니버스\texts" --dry-run
```
* 실제 파일 수정 없이 변경될 URL 목록을 미리 확인할 수 있습니다.

---

### 4. 디렉토리 내 전체 파일 일괄 변환
```bash
python .agents/skills/convert-suno-url/scripts/convert_suno_url.py "c:\dev\KLIEN\murdex\works\바스타즈 오브 더 유니버스\texts"
```
* 해당 폴더 안의 모든 `.txt` 및 `.md` 파일에서 Suno URL을 찾아 일괄 변환 및 업데이트합니다.

## 변환 규칙 (Internal Logic)

1. `https://suno.com/song/<UUID>` ➔ `<UUID>` 직접 추출 ➔ `https://cdn1.suno.ai/<UUID>.mp3`
2. `https://suno.com/s/<short_code>` ➔ HTTP 리디렉션 추적 ➔ HTML Meta (Canonical/og:image) 분석 ➔ `<UUID>` 추출 ➔ `https://cdn1.suno.ai/<UUID>.mp3`
