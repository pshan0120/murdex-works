"""장면 효과음을 코드로 만든다. 직접 합성한 소리라 저작권 문제가 없고, 같은 명령으로 언제든 다시 만들 수 있다.

  python gen_scene_sfx.py            # hospital/, impact/, device/ 폴더에 wav 생성

만드는 소리
  hospital/병원_심전도_비프.wav       일정한 간격의 심전도 모니터 비프음(1kHz) 6번
  impact/충격_쿵.wav                  커다랗고 묵직한 쿵 소리 한 번(메아리 없음)
  device/장치_판독기_스캔.wav         판독기가 손바닥을 훑는 상승 스캔음 → 인식이 끝났다는 확인음 두 번
"""
import os
import wave

import numpy as np

SR = 32000
HERE = os.path.dirname(os.path.abspath(__file__))


def fade(x, in_ms=0, out_ms=0):
    n_in, n_out = int(SR * in_ms / 1000), int(SR * out_ms / 1000)
    if n_in:
        x[:n_in] *= np.linspace(0, 1, n_in, dtype=np.float32)
    if n_out:
        x[-n_out:] *= np.linspace(1, 0, n_out, dtype=np.float32)
    return x


def silence(sec):
    return np.zeros(int(SR * sec), dtype=np.float32)


def beep(freq, sec, amp=0.3):
    t = np.arange(int(SR * sec)) / SR
    x = np.sin(2 * np.pi * freq * t) + 0.12 * np.sin(2 * np.pi * freq * 2 * t)
    return fade((x / 1.12 * amp).astype(np.float32), 6, 25)


def ecg_beeps(count=6, interval=0.95):
    """심전도 모니터: 짧고 맑은 비프가 일정한 간격으로 반복된다."""
    unit = np.concatenate([beep(1000, 0.14), silence(interval - 0.14)])
    return np.concatenate([silence(0.2)] + [unit] * count)


def lowpass(x, cutoff):
    spec = np.fft.rfft(x)
    freqs = np.fft.rfftfreq(len(x), 1 / SR)
    spec *= 1 / (1 + (freqs / cutoff) ** 4)
    return np.fft.irfft(spec, len(x)).astype(np.float32)


def thud():
    """커다랗고 묵직한 쿵 한 번(메아리 없음). 소리가 내려앉는 사인파는 전자오락의 '뿅' 소리처럼 들려서 쓰지 않고,
    마루나 큰 상자가 맞았을 때처럼 높이가 변하지 않는 여러 울림(공명)을 서로 다른 속도로 줄어들게 겹친다.
    여기에 부딪히는 순간의 둔탁한 잡음과 낮은 울림을 더한다."""
    n = int(SR * 1.3)
    t = np.arange(n) / SR
    rng = np.random.default_rng(21)
    # (주파수Hz, 줄어드는 속도, 크기): 일부러 정수배로 맞추지 않아 악기가 아니라 물체가 울리는 소리가 되게 한다
    modes = [(52, 5.0, 0.55), (76, 6.5, 0.8), (112, 8.5, 1.0), (158, 11, 0.95), (214, 14, 0.75), (291, 19, 0.55), (396, 27, 0.35)]
    body = np.zeros(n, dtype=np.float32)
    for f, d, a in modes:
        body += a * np.sin(2 * np.pi * f * t + rng.uniform(0, 2 * np.pi)) * np.exp(-t * d)
    slap = lowpass(rng.standard_normal(n).astype(np.float32), 1600) * np.exp(-t * 85) * 2.4   # 부딪히는 순간의 짧은 소리
    muffled = lowpass(rng.standard_normal(n).astype(np.float32), 650) * np.exp(-t * 15) * 3.4  # 둔탁하게 퍼지는 소리
    x = body * 0.6 + slap * 0.6 + muffled * 0.6
    x[: int(SR * 0.002)] *= np.linspace(0, 1, int(SR * 0.002), dtype=np.float32)
    x = np.tanh(1.4 * x) / np.tanh(1.4)                  # 아주 약하게만 눌러 소리를 단단하게 한다
    x = fade(x.astype(np.float32), 0, 160)
    return x / np.abs(x).max() * 0.9


def scanner():
    """손바닥을 훑는 상승 스캔음(깜빡이는 느낌의 떨림 포함) → 인식 완료 확인음 두 번."""
    n = int(SR * 1.1)
    t = np.arange(n) / SR
    f = 520 + 900 * (t / t[-1])
    phase = 2 * np.pi * np.cumsum(f) / SR
    pulse = 0.65 + 0.35 * np.sin(2 * np.pi * 14 * t)         # 스캔 불빛이 깜빡이는 듯한 떨림
    sweep = fade((np.sin(phase) * pulse * 0.22).astype(np.float32), 30, 80)
    ok = np.concatenate([beep(880, 0.11, 0.28), silence(0.05), beep(1320, 0.22, 0.28)])
    return np.concatenate([silence(0.1), sweep, silence(0.12), ok])


def save(folder, name, x):
    out = os.path.join(HERE, folder)
    os.makedirs(out, exist_ok=True)
    x = np.clip(x, -1, 1)
    pcm = (x * 32767).astype("<i2").tobytes()
    path = os.path.join(out, name)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm)
    print(f"{folder}/{name}: {len(x) / SR:.1f}초, {os.path.getsize(path) // 1024}KB, 최대 진폭 {np.abs(x).max():.2f}")


if __name__ == "__main__":
    save("hospital", "병원_심전도_비프.wav", ecg_beeps())
    save("impact", "충격_쿵.wav", thud())
    save("device", "장치_판독기_스캔.wav", scanner())
