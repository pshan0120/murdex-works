---
name: square-crop-image
description: 이미지를 정중앙을 기준으로 1:1 정사각형 비율로 크롭합니다. 대상 파일 또는 폴더 경로를 인자로 받아 처리합니다.
---

# Square Crop Image Skill

사용자가 특정 이미지 또는 특정 폴더 안의 이미지들을 1:1 (정사각형) 비율로 크롭해 달라고 요청할 때 이 스킬을 사용하세요.
이 스킬은 원본 이미지를 유지하고, 파일명 뒤에 `_cropped`가 붙은 새로운 이미지 파일을 생성합니다.

## 사용 방법

아래 명령어를 사용하여 스킬 스크립트를 실행하세요. `[대상_경로]`에는 단일 이미지 파일의 절대 경로 또는 폴더의 절대 경로를 입력합니다.

```powershell
python "c:\dev\KLIEN\murdex\works\.agents\skills\square-crop-image\scripts\crop.py" "[대상_경로]"
```

- 스크립트는 Python의 `Pillow` 라이브러리를 사용합니다. 만약 실행 시 Pillow가 없다는 에러가 발생하면, `pip install Pillow` 명령을 먼저 실행한 후 다시 시도하세요.
- 폴더 경로를 지정하면 해당 폴더 바로 아래에 있는 모든 이미지 파일을 자동으로 처리합니다.
- 이미 이름이 `_cropped`로 끝나는 파일이나, 이미 정사각형(1:1) 비율인 이미지는 안전하게 건너뜁니다.
