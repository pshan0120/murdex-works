"""단서 버튼을 눌렀을 때 쓰는 소리를 코드로 만든다. 직접 합성한 소리라 저작권 문제가 없고, 같은 명령으로 언제든 다시 만들 수 있다.

  python gen_clue_action_sfx.py        # paper/, bag/ 폴더에 wav 생성

만드는 소리 (목련다방 살인사건의 단서 버튼에서 쓴다)
  paper/종이_일기장_자물쇠_넘김.wav     자물쇠가 부러지는 짧은 쇳소리 뒤 일기장 종이가 두 번 넘어가는 소리 (일기장 읽어보기)
  paper/종이_신문지_바스락.wav          신문지를 벗겨낼 때의 바스락거림 (신문지 벗겨보기)
  paper/종이_봉투_찢는_소리.wav         풀로 봉인된 봉투를 찢어 여는 소리 (봉투 뜯어보기)
  bag/가방_지퍼_쏟아짐.wav              지퍼를 열고 가방을 털자 작은 물건들이 쏟아져 구르는 소리 (가방 털어보기)

같은 난수 씨앗을 써서 다시 만들어도 같은 소리가 나온다.
"""
import os
import wave

import numpy as np

SR = 32000
HERE = os.path.dirname(os.path.abspath(__file__))


def silence(sec):
    return np.zeros(int(SR * sec), dtype=np.float32)


def fade(x, in_ms=0, out_ms=0):
    x = x.copy()
    n_in, n_out = int(SR * in_ms / 1000), int(SR * out_ms / 1000)
    if n_in:
        x[:n_in] *= np.linspace(0, 1, n_in, dtype=np.float32)
    if n_out:
        x[-n_out:] *= np.linspace(1, 0, n_out, dtype=np.float32)
    return x


def spectrum_filter(x, low=None, high=None, order=4):
    """주파수 영역에서 high-pass(low 이상만 통과), low-pass(high 이하만 통과)를 건다."""
    spec = np.fft.rfft(x)
    freqs = np.fft.rfftfreq(len(x), 1 / SR)
    if low:
        spec *= 1 - 1 / (1 + (freqs / low) ** (2 * order))
    if high:
        spec *= 1 / (1 + (freqs / high) ** (2 * order))
    return np.fft.irfft(spec, len(x)).astype(np.float32)


def noise(rng, sec):
    return rng.standard_normal(int(SR * sec)).astype(np.float32)


def place(canvas, x, at_sec):
    """canvas의 at_sec 위치에 x를 더한다(길이를 넘으면 잘라낸다)."""
    start = int(SR * at_sec)
    end = min(len(canvas), start + len(x))
    if start < len(canvas):
        canvas[start:end] += x[: end - start]


def finish(x, peak=0.85, tail_ms=120):
    x = fade(x, 2, tail_ms)
    return (x / np.abs(x).max() * peak).astype(np.float32)


def page_flip(rng, sec=0.55, strength=1.0):
    """종이 한 장이 넘어가는 소리: 높은 쪽 바람 소리(휙)가 빠르게 커졌다 잦아들고, 끝에서 가볍게 내려앉는 소리가 난다."""
    n = int(SR * sec)
    t = np.arange(n) / SR
    swish = spectrum_filter(noise(rng, sec), low=1400, high=7500)
    rise = np.clip(t / (sec * 0.35), 0, 1) ** 1.6
    fall = np.exp(-np.clip(t - sec * 0.35, 0, None) * 7.0)
    env = rise * fall
    flutter = 0.75 + 0.25 * np.sin(2 * np.pi * 38 * t + rng.uniform(0, 6.28))  # 종이가 떨리는 느낌
    x = swish * env * flutter
    land = spectrum_filter(noise(rng, sec), low=300, high=1800) * np.exp(-np.clip(t - sec * 0.55, 0, None) * 45) * (t > sec * 0.55)
    return (x * 0.9 + land * 0.35) * strength


def lock_snap(rng):
    """작은 자물쇠가 부러지는 소리: 짧은 쇳소리(여러 높이의 맑은 울림이 빠르게 줄어듦) + 나무에 맞은 둔탁한 딱 소리."""
    n = int(SR * 0.6)
    t = np.arange(n) / SR
    metal = np.zeros(n, dtype=np.float32)
    for freq, decay, amp in [(2150, 38, 0.8), (3380, 52, 0.55), (5210, 75, 0.35), (1480, 30, 0.5)]:
        metal += amp * np.sin(2 * np.pi * freq * t + rng.uniform(0, 6.28)) * np.exp(-t * decay)
    click = spectrum_filter(noise(rng, 0.6), low=2500) * np.exp(-t * 320)
    thud = spectrum_filter(noise(rng, 0.6), high=700) * np.exp(-t * 38)
    return metal * 0.55 + click * 0.9 + thud * 0.7


def diary_open(rng):
    x = silence(2.6)
    place(x, lock_snap(rng), 0.05)
    place(x, page_flip(rng, 0.6, 1.0), 0.95)
    place(x, page_flip(rng, 0.5, 0.75), 1.75)
    return finish(x)


def newspaper_rustle(rng):
    """신문지를 벗겨낼 때의 바스락거림: 짧은 마찰음이 처음엔 빽빽하다가 점점 듬성해진다."""
    sec = 1.7
    x = silence(sec)
    base = spectrum_filter(noise(rng, sec), low=1800, high=9000)
    t = np.arange(len(x)) / SR
    slow = 0.35 + 0.65 * np.abs(spectrum_filter(noise(rng, sec), high=9))  # 천천히 세기가 흔들림
    x += base * slow * np.exp(-t * 1.5) * 0.35
    # 마찰음 알갱이: 시간이 갈수록 간격이 벌어진다
    at = 0.0
    while at < sec - 0.1:
        dur = rng.uniform(0.004, 0.03)
        grain = spectrum_filter(noise(rng, dur), low=rng.uniform(1500, 3500), high=rng.uniform(6000, 11000))
        grain *= np.hanning(len(grain)).astype(np.float32) * rng.uniform(0.3, 1.0) * np.exp(-at * 0.9)
        place(x, grain, at)
        at += rng.exponential(0.012 + 0.07 * (at / sec) ** 1.4)
    return finish(x, tail_ms=250)


def envelope_tear(rng):
    """봉투가 찢어지는 소리: 풀이 떨어지는 자잘한 소리로 시작해, 찢어지는 거친 소리가 빨라지며 커졌다 끊긴다."""
    sec = 1.3
    n = int(SR * sec)
    t = np.arange(n) / SR
    x = silence(sec)
    # 풀이 떨어지는 자잘한 딱딱 소리
    for at in np.sort(rng.uniform(0.0, 0.32, 9)):
        place(x, spectrum_filter(noise(rng, 0.012), low=2200) * np.hanning(int(SR * 0.012)).astype(np.float32) * rng.uniform(0.25, 0.6), at)
    # 찢어지는 소리: 거친 잡음에 빠른 불규칙 떨림을 곱한다
    start = 0.28
    m = int(SR * (sec - start))
    tt = np.arange(m) / SR
    rip = spectrum_filter(noise(rng, sec - start), low=1700, high=9500)
    jitter = np.clip(spectrum_filter(noise(rng, sec - start), high=70) * 6, -1, 1)  # 약 70Hz까지의 불규칙한 요동
    speed = 0.55 + 0.45 * np.abs(jitter)
    env = np.clip(tt / 0.45, 0, 1) ** 1.3 * np.exp(-np.clip(tt - 0.5, 0, None) * 5.5)
    place(x, rip * speed * env * 0.9, start)
    return finish(x, tail_ms=200)


def bag_spill(rng):
    """지퍼를 여는 소리(톱니가 빠르게 이어짐) 뒤, 가방을 털자 작은 물건들이 쏟아져 바닥에 구르는 소리."""
    sec = 2.4
    x = silence(sec)
    # 지퍼: 아주 짧은 틱이 점점 빨라지며 이어진다
    at, rate = 0.05, 38.0
    while at < 0.55:
        tick = spectrum_filter(noise(rng, 0.004), low=2600) * np.hanning(int(SR * 0.004)).astype(np.float32) * 0.5
        place(x, tick, at)
        at += 1.0 / rate
        rate = min(rate * 1.012, 80)
    # 쏟아지는 물건들: 작은 금속, 플라스틱, 나무 조각이 서로 다른 높이로 울리며 튕긴다. 처음엔 빽빽하고 점점 듬성해진다
    at = 0.75
    while at < sec - 0.2:
        freq = rng.choice([rng.uniform(900, 1600), rng.uniform(1800, 3200), rng.uniform(3600, 5200)])
        decay = rng.uniform(70, 260)
        dur = min(0.35, 6 / decay)
        t = np.arange(int(SR * dur)) / SR
        piece = np.sin(2 * np.pi * freq * t + rng.uniform(0, 6.28)) * np.exp(-t * decay)
        piece += 0.4 * np.sin(2 * np.pi * freq * 2.76 * t) * np.exp(-t * decay * 1.6)  # 정수배가 아닌 배음으로 물체 소리처럼
        amp = rng.uniform(0.25, 0.9) * np.exp(-(at - 0.75) * 0.9)
        place(x, piece.astype(np.float32) * amp, at)
        if rng.random() < 0.18:   # 가끔 묵직한 물건이 바닥에 툭 떨어진다
            thud = spectrum_filter(noise(rng, 0.12), high=rng.uniform(350, 700)) * np.exp(-np.arange(int(SR * 0.12)) / SR * 38)
            place(x, thud * amp * 2.2, at)
        at += rng.exponential(0.018 + 0.13 * ((at - 0.75) / (sec - 0.75)) ** 1.3)
    return finish(x, tail_ms=300)


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
    rms = float(np.sqrt(np.mean(x ** 2)))
    print(f"{folder}/{name}: {len(x) / SR:.1f}초, {os.path.getsize(path) // 1024}KB, 최대 진폭 {np.abs(x).max():.2f}, 평균 세기(RMS) {rms:.3f}")


if __name__ == "__main__":
    save("paper", "종이_일기장_자물쇠_넘김.wav", diary_open(np.random.default_rng(101)))
    save("paper", "종이_신문지_바스락.wav", newspaper_rustle(np.random.default_rng(102)))
    save("paper", "종이_봉투_찢는_소리.wav", envelope_tear(np.random.default_rng(103)))
    save("bag", "가방_지퍼_쏟아짐.wav", bag_spill(np.random.default_rng(104)))
