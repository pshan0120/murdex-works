#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
합쳐진 대본 음성 mp3를 Cloudinary에 업로드하고(크리에이터 화면의 "BGM 업로드"와
동일한 /api/storage/upload/audio 엔드포인트 사용), 받은 URL을 대상 단계_*.txt의
"대본 낭독" <audio> 태그 src에 채워 넣는 스크립트 (upload_script_audio.py)

DB에는 아무것도 쓰지 않는다 (대본음성 URL은 story_step 테이블 컬럼이 아니라
단계 설명 HTML 안 <audio> 태그로만 존재하는 값이라서, txt 파일 수정으로 충분함).
로컬 개발 서버(localhost)에 대해서만 동작한다 — 실서버 토큰을 흉내내는 용도가 아님.
"""

import argparse
import os
import re
import sys
from urllib.parse import urlparse

sys.stdout.reconfigure(encoding="utf-8")

API_DIR = r"c:\dev\KLIEN\murdex\murdex-api"
if API_DIR not in sys.path:
    sys.path.insert(0, API_DIR)


def parse_args():
    parser = argparse.ArgumentParser(
        description="합쳐진 mp3를 업로드하고 단계 파일의 <audio src>를 채웁니다."
    )
    parser.add_argument("mp3_path", help="업로드할 mp3 파일 경로 (concat-voice-wav 결과물)")
    parser.add_argument("step_txt_path", help="src를 채워 넣을 단계_*.txt 경로")
    parser.add_argument("--api-url", default="http://localhost:8601", help="murdex-api 주소 (로컬 전용)")
    return parser.parse_args()


def get_step_story_id(step_txt_path):
    with open(step_txt_path, "r", encoding="utf-8") as f:
        content = f.read()
    match = re.search(r"StoryID\s*:\s*([a-fA-F0-9\-]+)", content)
    if not match:
        raise ValueError(f"StoryID를 찾지 못했습니다: {step_txt_path}")
    return match.group(1).strip()


def get_story_creator_id(story_id):
    import asyncio
    from config.di_container import di_container

    async def _fetch():
        story_repository = di_container.get_story_repository()
        story = await story_repository.get_by_id(story_id)
        if not story:
            raise ValueError(f"StoryID로 작품을 찾지 못했습니다: {story_id}")
        return story.creator_id

    return asyncio.run(_fetch())


def mint_local_jwt(member_id):
    from domain.auth.infrastructure.jwt_utils import JWTUtils
    return JWTUtils.create_access_token({"sub": member_id})


def upload_audio(api_url, mp3_path, token):
    import requests

    with open(mp3_path, "rb") as f:
        files = {"file": (os.path.basename(mp3_path), f, "audio/mpeg")}
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.post(f"{api_url}/api/storage/upload/audio", files=files, headers=headers, timeout=60)

    resp.raise_for_status()
    data = resp.json()
    if not data.get("success"):
        raise RuntimeError(f"업로드 실패: {data}")
    return data["data"]["url"]


def update_source_tag(step_txt_path, new_url):
    with open(step_txt_path, "r", encoding="utf-8") as f:
        content = f.read()

    # <audio> 태그가 섹션 제목 바로 뒤에 있는지, 안내 문단 뒤에 있는지 등 정확한 위치는
    # 파일마다 조금씩 다를 수 있어서(작가가 직접 문구/배치를 손보기도 함), section-title에
    # 앵커를 걸지 않고 <source ... type="audio/mpeg" ...> 태그 자체만 찾아 src를 바꾼다.
    # 단계 파일 안에서 이 타입의 source 태그는 대본 음성 하나뿐이라는 전제.
    pattern = re.compile(r'(<source src=")[^"]*("\s*type="audio/mpeg"\s*/?>)')

    matches = pattern.findall(content)
    if not matches:
        raise ValueError(
            "<source src=\"...\" type=\"audio/mpeg\" /> 태그를 찾지 못했습니다. "
            "gen-voice-wav 안내대로 미리 빈 audio 태그가 삽입되어 있는지 확인하세요."
        )
    if len(matches) > 1:
        raise ValueError(
            f"audio/mpeg source 태그가 {len(matches)}개 발견되어 어느 것을 바꿔야 할지 애매합니다. "
            "파일을 직접 확인하세요."
        )

    new_content, count = pattern.subn(rf"\g<1>{new_url}\g<2>", content)

    with open(step_txt_path, "w", encoding="utf-8") as f:
        f.write(new_content)


def main():
    args = parse_args()

    host = urlparse(args.api_url).hostname
    if host not in ("localhost", "127.0.0.1"):
        print(f"[ERROR] 이 스킬은 로컬 개발 서버 전용입니다 (localhost만 허용). 받은 주소: {args.api_url}")
        sys.exit(1)

    if not os.path.exists(args.mp3_path):
        print(f"[ERROR] mp3 파일을 찾을 수 없습니다: {args.mp3_path}")
        sys.exit(1)
    if not os.path.exists(args.step_txt_path):
        print(f"[ERROR] 단계 파일을 찾을 수 없습니다: {args.step_txt_path}")
        sys.exit(1)

    print("[INFO] 단계 파일에서 StoryID -> 작품 작가(member_id) 조회 중...")
    story_id = get_step_story_id(args.step_txt_path)
    creator_id = get_story_creator_id(story_id)
    print(f"[INFO] creator_id={creator_id}")

    token = mint_local_jwt(creator_id)

    print(f"[INFO] 업로드 중: {args.mp3_path}")
    url = upload_audio(args.api_url, args.mp3_path, token)
    print(f"[INFO] 업로드 완료: {url}")

    update_source_tag(args.step_txt_path, url)
    print(f"[DONE] {args.step_txt_path} 의 <audio src>를 갱신했습니다.")


if __name__ == "__main__":
    main()
