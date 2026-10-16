"""전화 효과음을 코드로 만든다. 직접 합성한 소리라 저작권 문제가 없고, 같은 명령으로 언제든 다시 만들 수 있다.

  python gen_phone_sfx.py            # phone/ 폴더에 wav 생성

만드는 소리
  전화_발신_연결음.wav  휴대폰 발신: 터치음 → 연결음(미국 방식 440Hz+480Hz) 2번 → 상대가 받는 딸깍
"""
import os
import wave

import numpy as np

SR = 32000  # 샘플링 속도(Hz). 말소리가 아니라 신호음이라 이 정도면 충분하다.
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "phone")


def silence(sec):
    return np.zeros(int(SR * sec), dtype=np.float32)


def fade(x, ms=12):
    n = min(len(x) // 2, int(SR * ms / 1000))
    if n:
        ramp = np.linspace(0, 1, n, dtype=np.float32)
        x[:n] *= ramp
        x[-n:] *= ramp[::-1]
    return x


def tone(freqs, sec, amp=0.22):
    t = np.arange(int(SR * sec)) / SR
    x = sum(np.sin(2 * np.pi * f * t) for f in freqs) / len(freqs)
    return fade((x * amp).astype(np.float32))


def click(sec=0.045, f=1500, amp=0.35):
    """짧은 터치음/딸깍: 빠르게 줄어드는 소리에 약한 잡음을 섞는다."""
    rng = np.random.default_rng(7)
    n = int(SR * sec)
    t = np.arange(n) / SR
    env = np.exp(-t * 90)
    x = (np.sin(2 * np.pi * f * t) * 0.6 + rng.standard_normal(n) * 0.4) * env
    return (x * amp).astype(np.float32)


def phone_call_ringback():
    ring = tone([440, 480], 2.0)          # 미국 연결음: 2초 울림
    parts = [
        silence(0.15), click(), silence(0.55),   # 통화 버튼을 누르는 터치음
        ring, silence(1.3), ring, silence(0.5),  # 연결음 2번(게임용으로 쉬는 시간을 줄임)
        click(0.06, 900, 0.3), silence(0.2),     # 상대가 받는 딸깍
    ]
    return np.concatenate(parts)


def save(name, x):
    os.makedirs(OUT, exist_ok=True)
    x = np.clip(x, -1, 1)
    pcm = (x * 32767).astype("<i2").tobytes()
    path = os.path.join(OUT, name)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm)
    print(f"{name}: {len(x) / SR:.1f}초, {os.path.getsize(path) // 1024}KB")


if __name__ == "__main__":
    save("전화_발신_연결음.wav", phone_call_ringback())
