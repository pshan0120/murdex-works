"""생활, 자연, 연출용 효과음을 코드로 만든다. 직접 합성한 소리라 저작권 문제가 없고, 같은 명령으로 언제든 다시 만들 수 있다.

  python gen_ambient_sfx.py            # phone/, clock/, steps/, stationery/, nature/, magic/ 폴더에 wav 생성
                                       # (phone/전화_발신_연결음.wav 가 먼저 있어야 한다: gen_phone_sfx.py)

만드는 소리
  phone/전화_수신_벨.wav             휴대폰 수신 벨: 높낮이가 번갈아 울리는 짧은 신호 4번 x 2회
  phone/전화_발신_연결음_바람.wav    발신 연결음 위에 바람 소리를 깔아, 바람 부는 곳에서 거는 통화
  clock/시계_초침_째깍.wav           조용한 방의 벽시계 초침(1초에 한 번 또렷한 틱)
  steps/발소리_하이힐_멀어짐.wav     하이힐이 복도를 따라 멀어지는 또각 소리
  steps/발소리_복도_멀어짐.wav       두 사람의 발소리가 복도 끝으로 멀어짐
  stationery/펜_뚜껑_딸깍.wav        펜 뚜껑을 여는 작은 소리
  nature/바람_돌풍.wav               몰아치는 바람(약 3초, 돌풍이 커졌다 잦아듦)
  nature/썰물_자갈_끌림.wav          썰물이 자갈을 끌고 내려가는 소리
  magic/마법_돌_울림.wav             돌에서 은은한 빛이 새어 나올 때의 신비로운 울림(반짝이는 높은 소리 없이 낮고 부드러운 울림만)
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


def band(x, lo=None, hi=None, order=4):
    """주파수 영역에서 낮은 쪽(lo)과 높은 쪽(hi)을 깎아 원하는 대역만 남긴다."""
    spec = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    if hi:
        spec = spec / (1 + (f / hi) ** order)
    if lo:
        spec = spec * (1 - 1 / (1 + (f / lo) ** order))
    return np.fft.irfft(spec, len(x)).astype(np.float32)


def smooth_random(n, rate_hz, rng):
    """천천히 오르내리는 0~1 사이의 불규칙한 값(돌풍, 파도의 세기에 쓴다)."""
    k = max(int(SR / rate_hz), 1)
    pts = rng.random(n // k + 3).astype(np.float32)
    return np.interp(np.arange(n), np.arange(len(pts)) * k, pts).astype(np.float32)


def tone(freq, sec, amp=0.3, harmonics=()):
    t = np.arange(int(SR * sec)) / SR
    x = np.sin(2 * np.pi * freq * t)
    for h, a in harmonics:
        x = x + a * np.sin(2 * np.pi * freq * h * t)
    return fade((x * amp / (1 + sum(a for _, a in harmonics))).astype(np.float32), 5, 15)


# --- 전화 ---------------------------------------------------------------
def phone_ring():
    burst = np.concatenate([tone(1046, 0.1, 0.3, [(2, 0.2)]), silence(0.04), tone(1318, 0.1, 0.3, [(2, 0.2)]), silence(0.04)] * 2)
    ring = np.concatenate([burst, silence(0.1), burst])
    return np.concatenate([silence(0.1), ring, silence(0.9), ring, silence(0.3)])


def wind_bed(n, amp, seed=3, gust_rate=0.45, depth=0.8):
    rng = np.random.default_rng(seed)
    noise = band(rng.standard_normal(n).astype(np.float32), lo=150, hi=1300)
    gust = (1 - depth) + depth * smooth_random(n, gust_rate, rng)
    x = noise * gust
    return x / np.abs(x).max() * amp


def phone_ring_with_wind():
    with wave.open(os.path.join(HERE, "phone", "전화_발신_연결음.wav")) as f:
        base = np.frombuffer(f.readframes(f.getnframes()), "<i2").astype(np.float32) / 32768
    return base + wind_bed(len(base), 0.09, seed=4)


# --- 시계, 문구 -----------------------------------------------------------
def clock_tick(seconds=5.0, gap=1.0):
    """벽시계 초침: 1초에 한 번, 같은 소리로 틱. 또렷한 딸깍에 시계통이 울리는 소리를 조금만 더한다."""
    rng = np.random.default_rng(8)
    out = np.zeros(int(SR * seconds), dtype=np.float32)
    for i in range(int((seconds - 0.4) / gap) + 1):
        n = int(SR * 0.22)
        t = np.arange(n) / SR
        click = (np.sin(2 * np.pi * 2300 * t) * 0.45 + np.sin(2 * np.pi * 3400 * t) * 0.25 + rng.standard_normal(n) * 0.5) * np.exp(-t * 110)
        click = band(click.astype(np.float32), lo=900, hi=6500)
        knock = np.sin(2 * np.pi * 520 * t) * np.exp(-t * 55)                                   # 시계통이 가볍게 울리는 소리
        x = click * 1.3 + knock * 0.35
        s0 = int(SR * (0.15 + i * gap))
        out[s0:s0 + n] += x.astype(np.float32)
    return out / np.abs(out).max() * 0.7


def pen_cap_click():
    rng = np.random.default_rng(2)

    def click(f, amp, decay):
        n = int(SR * 0.05)
        t = np.arange(n) / SR
        x = (np.sin(2 * np.pi * f * t) * 0.7 + rng.standard_normal(n) * 0.4) * np.exp(-t * decay)
        return band(x.astype(np.float32), lo=800, hi=6500) * amp
    out = np.zeros(int(SR * 0.45), dtype=np.float32)
    for st, f, a, d in ((0.05, 3300, 0.55, 140), (0.17, 2200, 0.4, 110)):   # 뚜껑이 빠지는 소리, 이어 걸림쇠 풀리는 소리
        c = click(f, a, d)
        s = int(SR * st)
        out[s:s + len(c)] += c
    return fade(out, 0, 60)


# --- 발소리 ---------------------------------------------------------------
def heel_walk(steps=9, start=0.1, gap=0.5):
    """하이힐: 딱딱한 굽 소리에 바닥을 울리는 낮은 몸통 소리를 더해 묵직하게 한다."""
    rng = np.random.default_rng(12)
    out = np.zeros(int(SR * (start + steps * gap + 0.9)), dtype=np.float32)
    for i in range(steps):
        dist = i / (steps - 1)                          # 0(가까움) -> 1(멀어짐)
        g = (1 - dist) ** 1.4
        n = int(SR * 0.22)
        t = np.arange(n) / SR
        f = 1500 if i % 2 == 0 else 1350               # 좌우 발 높이를 조금 다르게
        click = (np.sin(2 * np.pi * f * t) * 0.45 + rng.standard_normal(n) * 0.55) * np.exp(-t * 60)
        click = band(click.astype(np.float32), lo=500, hi=3800 - 2200 * dist)
        body = np.sin(2 * np.pi * (170 if i % 2 == 0 else 150) * t) * np.exp(-t * 26) * 1.0     # 바닥이 울리는 낮은 소리
        thud = band(rng.standard_normal(n).astype(np.float32), hi=520 - 200 * dist) * np.exp(-t * 32) * 2.2
        x = click * 1.2 + body * 0.45 + thud * 0.55
        s0 = int(SR * (start + i * gap + rng.uniform(-0.015, 0.015)))
        out[s0:s0 + n] += x.astype(np.float32) * g
    return fade(out / np.abs(out).max() * 0.8, 0, 200)


def corridor_steps(steps=7, start=0.1, gap=0.56):
    rng = np.random.default_rng(15)
    out = np.zeros(int(SR * (start + (steps + 1) * gap + 1.0)), dtype=np.float32)
    for who, shift in ((0, 0.0), (1, 0.27)):          # 두 사람의 걸음이 엇갈리게 겹친다
        for i in range(steps):
            dist = (i + shift) / steps
            g = (1 - dist) ** 1.8 * (1.0 if who == 0 else 0.8)
            n = int(SR * 0.16)
            t = np.arange(n) / SR
            thump = band(rng.standard_normal(n).astype(np.float32), hi=700 - 280 * dist) * np.exp(-t * 20) * 3.0
            body = np.sin(2 * np.pi * 140 * t) * np.exp(-t * 24) * 0.6
            scuff = band(rng.standard_normal(n).astype(np.float32), lo=900, hi=2800 - 1600 * dist) * np.exp(-t * 40) * 0.5
            x = thump + body + scuff * 1.1
            s = int(SR * (start + (i + shift) * gap + rng.uniform(-0.02, 0.02)))
            out[s:s + n] += x * g
    return fade(out / np.abs(out).max() * 0.8, 0, 250)


# --- 자연 -----------------------------------------------------------------
def gust_wind(seconds=3.0):
    n = int(SR * seconds)
    x = wind_bed(n, 0.5, seed=5, gust_rate=0.9, depth=0.95)
    return fade(x, 300, 700)


def ebb_pebbles(seconds=8.0):
    rng = np.random.default_rng(31)
    n = int(SR * seconds)
    t = np.arange(n) / SR
    swell = 0.5 - 0.5 * np.cos(2 * np.pi * t / 4.0)                    # 4초마다 밀려왔다 빠지는 물결
    grad = -np.gradient(swell)
    retreat = np.clip(grad / grad.max(), 0, 1) ** 0.6                   # 물이 빠지는 순간에 자갈이 끌린다
    water = band(rng.standard_normal(n).astype(np.float32), lo=250, hi=2200) * swell
    water = water / np.abs(water).max() * 0.35
    pebbles = np.zeros(n, dtype=np.float32)
    for pos in rng.integers(0, n - 800, int(seconds * 90)):
        if rng.random() < retreat[pos]:
            m = 600
            tt = np.arange(m) / SR
            pebbles[pos:pos + m] += band(rng.standard_normal(m).astype(np.float32), lo=1500, hi=5200) * np.exp(-tt * 380) * rng.uniform(0.2, 1.0)
    pebbles = pebbles / np.abs(pebbles).max() * 0.28
    return fade(water + pebbles, 600, 900)


# --- 연출 -----------------------------------------------------------------
def magic_stone_hum(seconds=5.5):
    rng = np.random.default_rng(40)
    n = int(SR * seconds)
    t = np.arange(n) / SR
    x = np.zeros(n, dtype=np.float32)
    for f, a in ((196, 0.5), (294, 0.4), (392, 0.35), (588, 0.25), (784, 0.18)):
        for det in (-0.7, 0.0, 0.8):                                    # 살짝 어긋난 소리를 겹쳐 울렁이게 한다
            trem = 0.75 + 0.25 * np.sin(2 * np.pi * rng.uniform(0.2, 0.6) * t + rng.uniform(0, 6))
            x += (a / 3) * np.sin(2 * np.pi * (f + det) * t + rng.uniform(0, 6)) * trem
    env = np.minimum(t / 1.6, 1.0) * np.minimum((seconds - t) / 2.2, 1.0)
    x = x * env
    return x / np.abs(x).max() * 0.45


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
    save("phone", "전화_수신_벨.wav", phone_ring())
    save("phone", "전화_발신_연결음_바람.wav", phone_ring_with_wind())
    save("clock", "시계_초침_째깍.wav", clock_tick())
    save("steps", "발소리_하이힐_멀어짐.wav", heel_walk())
    save("steps", "발소리_복도_멀어짐.wav", corridor_steps())
    save("stationery", "펜_뚜껑_딸깍.wav", pen_cap_click())
    save("nature", "바람_돌풍.wav", gust_wind())
    save("nature", "썰물_자갈_끌림.wav", ebb_pebbles())
    save("magic", "마법_돌_울림.wav", magic_stone_hum())
