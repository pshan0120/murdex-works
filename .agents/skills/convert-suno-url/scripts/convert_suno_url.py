#!/usr/bin/env python3
"""
convert_suno_url.py

Suno AI 공유 링크(https://suno.com/s/... 또는 https://suno.com/song/...)를 감지하여
직접 재생이 가능한 CDN MP3 URL(https://cdn1.suno.ai/<UUID>.mp3)로 변환하는 스크립트.
"""

import sys
import os
import re
import argparse
import urllib.request
import urllib.error

SUNO_SHORT_PATTERN = re.compile(r'https?://suno\.com/s/([a-zA-Z0-9_-]+)')
SUNO_SONG_PATTERN = re.compile(r'https?://suno\.com/song/([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})')

def resolve_suno_uuid(url: str) -> str | None:
    """Suno URL에서 UUID를 추출하거나 리디렉션을 추적하여 UUID를 반환합니다."""
    # 1. 이미 song URL 형태인 경우 바로 UUID 추출
    song_match = SUNO_SONG_PATTERN.search(url)
    if song_match:
        return song_match.group(1)

    # 2. 숏링크(https://suno.com/s/...)인 경우 HTTP 요청으로 최종 URL 및 HTML 원본 탐색
    short_match = SUNO_SHORT_PATTERN.search(url)
    if not short_match:
        return None

    try:
        req = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            final_url = response.geturl()
            song_match = SUNO_SONG_PATTERN.search(final_url)
            if song_match:
                return song_match.group(1)
            
            # 리디렉션 주소에 없으면 HTML 내용 내 canonical 또는 og:image에서 UUID 탐색
            content = response.read().decode('utf-8', errors='ignore')
            uuid_match = re.search(r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', content)
            if uuid_match:
                return uuid_match.group(0)
    except Exception as e:
        print(f"[ERROR] Failed to resolve Suno URL ({url}): {e}", file=sys.stderr)

    return None

def convert_suno_url_string(url: str) -> str | None:
    """Suno URL을 cdn1.suno.ai direct MP3 URL로 변환합니다."""
    uuid = resolve_suno_uuid(url)
    if not uuid:
        return None
    return f"https://cdn1.suno.ai/{uuid}.mp3"

def process_file(file_path: str, dry_run: bool = False) -> int:
    """텍스트 파일 내 Suno 링크를 탐색하여 CDN URL로 치환합니다."""
    if not os.path.exists(file_path):
        print(f"[WARN] File not found: {file_path}", file=sys.stderr)
        return 0

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Suno URL 감지 (suno.com/s/... 또는 suno.com/song/...)
    urls = set(SUNO_SHORT_PATTERN.findall(content) + SUNO_SONG_PATTERN.findall(content))
    matches = re.findall(r'https?://suno\.com/(?:s|song)/[a-zA-Z0-9_-]+', content)
    if not matches:
        return 0

    replacements = {}
    for match_url in set(matches):
        direct_url = convert_suno_url_string(match_url)
        if direct_url:
            replacements[match_url] = direct_url
            print(f"[CONVERT] {match_url} -> {direct_url}")

    if not replacements:
        return 0

    new_content = content
    for old_url, new_url in replacements.items():
        new_content = new_content.replace(old_url, new_url)

    if dry_run:
        print(f"[DRY-RUN] Would update file: {file_path}")
    else:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"[UPDATED] {file_path}")

    return len(replacements)

def process_path(target_path: str, dry_run: bool = False):
    """단일 파일 또는 디렉토리 내 txt 파일들을 처리합니다."""
    if os.path.isfile(target_path):
        process_file(target_path, dry_run)
        return

    if os.path.isdir(target_path):
        count = 0
        for root, _, files in os.walk(target_path):
            for file in files:
                if file.endswith('.txt') or file.endswith('.md'):
                    full_path = os.path.join(root, file)
                    count += process_file(full_path, dry_run)
        print(f"[SUMMARY] Total {count} Suno URL(s) converted.")

def main():
    parser = argparse.ArgumentParser(description="Suno AI URL to Direct CDN MP3 Converter")
    parser.add_argument("target", help="Suno URL string, text file path, or directory path")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without modifying files")

    args = parser.parse_args()

    # 입력값이 URL인 경우
    if args.target.startswith("http://") or args.target.startswith("https://"):
        res = convert_suno_url_string(args.target)
        if res:
            print(f"Direct CDN MP3 URL: {res}")
        else:
            print("[ERROR] Could not resolve Suno URL.", file=sys.stderr)
            sys.exit(1)
        return

    process_path(args.target, args.dry_run)

if __name__ == "__main__":
    main()
