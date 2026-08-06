#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WAV 대사 음성 파일 병합 스크립트 (concat_voice_wav.py)
FFmpeg concat demuxer 방식을 사용하여 대사 사이 무음 삽입 및 정렬을 완벽하게 수행합니다.
"""

import argparse
import glob
import os
import re
import subprocess
import sys
import tempfile
import wave
import struct

try:
    import imageio_ffmpeg
    FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()
except Exception as e:
    FFMPEG_EXE = "ffmpeg"


def natural_sort_key(s):
    """문자열 내의 숫자를 자연스러운 숫자 순서(1, 2, ..., 9, 10)로 정렬하기 위한 키 함수"""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]


def parse_args():
    parser = argparse.ArgumentParser(description="대사 WAV 음성 파일들을 무음 간격과 함께 순서대로 하나의 MP3 파일로 병합합니다.")
    parser.add_argument("inputs", nargs="+", help="WAV 파일 경로, 폴더 경로 또는 와일드카드 패턴 (예: voice_*.wav)")
    parser.add_argument("-o", "--output", help="최종 출력 MP3 파일 경로")
    parser.add_argument("-p", "--pause-sec", type=float, default=0.6, help="대사 사이의 무음(지연) 시간(초 단위, 기본값: 0.6초)")
    parser.add_argument("--bitrate", default="192k", help="MP3 비트레이트 (기본값: 192k)")
    return parser.parse_args()


def resolve_files(input_patterns):
    files = []
    for pattern in input_patterns:
        if os.path.isdir(pattern):
            found = glob.glob(os.path.join(pattern, "*.wav"))
            files.extend(found)
        else:
            found = glob.glob(pattern)
            if found:
                files.extend(found)
            elif os.path.exists(pattern):
                files.append(pattern)
    
    files = sorted(list(set(files)), key=natural_sort_key)
    return files


def create_silence_wav(filepath, duration_sec, sample_rate=44100, channels=1):
    """파이썬 wave 모듈로 무음 WAV 생성"""
    n_samples = int(sample_rate * duration_sec)
    silence_data = struct.pack(f'<{n_samples * channels}h', *([0] * (n_samples * channels)))
    with wave.open(filepath, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(silence_data)


def main():
    args = parse_args()
    file_list = resolve_files(args.inputs)

    if not file_list:
        print("[ERROR] 병합할 WAV 파일을 찾지 못했습니다.", file=sys.stderr)
        sys.exit(1)

    print(f"[INFO] 총 {len(file_list)}개의 WAV 파일을 발견하였습니다.")
    for idx, fpath in enumerate(file_list, 1):
        print(f"  {idx}. {os.path.basename(fpath)}")

    output_path = args.output
    if not output_path:
        first_dir = os.path.dirname(file_list[0])
        first_name = os.path.splitext(os.path.basename(file_list[0]))[0]
        clean_prefix = re.sub(r'[\s_]*\d+$', '', first_name)
        if not clean_prefix:
            clean_prefix = "merged_dialogue"
        output_path = os.path.join(first_dir, f"{clean_prefix}.mp3")

    # 첫 번째 WAV 오디오 정보 추출
    sample_rate = 44100
    channels = 1
    try:
        with wave.open(file_list[0], 'rb') as wf:
            sample_rate = wf.getframerate()
            channels = wf.getnchannels()
    except Exception:
        pass

    # 임시 디렉토리에서 작업
    with tempfile.TemporaryDirectory() as temp_dir:
        silence_path = os.path.join(temp_dir, "silence.wav")
        pause_sec = args.pause_sec
        if pause_sec > 0:
            create_silence_wav(silence_path, pause_sec, sample_rate, channels)

        # concat list 파일 작성
        list_file_path = os.path.join(temp_dir, "concat_list.txt")
        with open(list_file_path, "w", encoding="utf-8") as f:
            for idx, fpath in enumerate(file_list):
                abs_path = os.path.abspath(fpath).replace("\\", "/")
                f.write(f"file '{abs_path}'\n")
                if pause_sec > 0 and idx < len(file_list) - 1:
                    abs_silence = os.path.abspath(silence_path).replace("\\", "/")
                    f.write(f"file '{abs_silence}'\n")

        # FFmpeg 명령어 실행
        cmd = [
            FFMPEG_EXE, "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", list_file_path,
            "-c:a", "libmp3lame",
            "-b:a", args.bitrate,
            output_path
        ]

        out_dir = os.path.dirname(output_path)
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)

        print(f"[INFO] 병합 진행 중... (대사 간격: {pause_sec}초)")
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')

        if result.returncode == 0:
            print(f"[SUCCESS] 병합 완료! 출력 파일: {output_path}")
        else:
            print(f"[ERROR] FFmpeg 실행 중 오류가 발생했습니다.\n{result.stderr}", file=sys.stderr)
            sys.exit(result.returncode)


if __name__ == "__main__":
    main()
