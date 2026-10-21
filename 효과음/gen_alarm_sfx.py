"""경보 효과음을 코드로 만든다. 직접 합성한 소리라 저작권 문제가 없고, 같은 명령으로 언제든 다시 만들 수 있다.

  python gen_alarm_sfx.py            # alarm/, broadcast/ 폴더에 wav 생성

만드는 소리
  alarm/경보_비상_사이렌.wav        오르내리는 사이렌 3번 → 천천히 잦아듦 (사이렌만, 다른 소리 없음)
  broadcast/방송_스피커_지직.wav    천장 스피커가 켜질 때의 지직거림 (사이렌 없음)
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


def lowpass(x, cutoff=3200):
    """너무 날카롭지 않게, 건물 천장 스피커에서 나오는 듯 높은 소리를 눌러 준다."""
    spec = np.fft.rfft(x)
    freqs = np.fft.rfftfreq(len(x), 1 / SR)
    spec *= 1 / (1 + (freqs / cutoff) ** 4)
    return np.fft.irfft(spec, len(x)).astype(np.float32)


def speaker_static(sec=1.7, amp=0.32):
    """스피커가 켜질 때의 소리: 처음의 퍽 하는 잡음, 띄엄띄엄 끊기는 지직거림, 낮게 깔린 웅 소리, 마지막 딸깍."""
    rng = np.random.default_rng(11)
    n = int(SR * sec)
    t = np.arange(n) / SR
    noise = rng.standard_normal(n).astype(np.float32)
    # 높은 쪽 잡음만 남겨 지직거리는 느낌으로 만든다(낮은 소리를 깎아 낸다)
    spec = np.fft.rfft(noise)
    freqs = np.fft.rfftfreq(n, 1 / SR)
    spec *= (freqs > 900) / (1 + (freqs / 6000) ** 2)
    hiss = np.fft.irfft(spec, n).astype(np.float32)
    hiss /= np.abs(hiss).max()
    gate = (rng.random(n // 480 + 1) > 0.4).astype(np.float32).repeat(480)[:n]
    gate = np.convolve(gate, np.ones(40, dtype=np.float32) / 40, mode="same")  # 끊기는 경계를 조금 부드럽게
    env = np.exp(-t * 0.9)
    hum = (np.sin(2 * np.pi * 120 * t) * 0.5 + np.sin(2 * np.pi * 60 * t) * 0.5) * np.minimum(t / 0.2, 1) * np.minimum((sec - t) / 0.3, 1)
    pop = np.zeros(n, dtype=np.float32)
    pn = int(SR * 0.05)
    pop[:pn] = rng.standard_normal(pn) * np.exp(-np.arange(pn) / SR * 80) * 0.9
    x = hiss * gate * env * amp + hum * amp * 0.25 + pop * amp
    x[-int(SR * 0.04):] = x[-int(SR * 0.04):] * np.linspace(1, 0, int(SR * 0.04), dtype=np.float32)
    return x.astype(np.float32)


def wail(cycles=3, period=1.9, lo=620, hi=1180, amp=0.28):
    """주파수가 낮은 음에서 높은 음으로 올라갔다 내려오는 사이렌."""
    n = int(SR * period * cycles)
    t = np.arange(n) / SR
    tri = 1 - np.abs(2 * ((t / period) % 1) - 1)          # 0→1→0 삼각파
    f = lo + (hi - lo) * tri
    phase = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(phase) + 0.35 * np.sin(2 * phase) + 0.18 * np.sin(3 * phase)  # 경보기 같은 거친 음색
    x = (x / 1.6 * amp).astype(np.float32)
    return fade(lowpass(x), 40, 900)


def emergency_siren():
    return np.concatenate([np.zeros(int(SR * 0.1), dtype=np.float32), wail()])


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
    print(f"{name}: {len(x) / SR:.1f}초, {os.path.getsize(path) // 1024}KB, 최대 진폭 {np.abs(x).max():.2f}")


if __name__ == "__main__":
    save("alarm", "경보_비상_사이렌.wav", emergency_siren())
    save("broadcast", "방송_스피커_지직.wav", speaker_static())
