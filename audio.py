"""Synthesized audio bus for Declare.

We don't ship audio files. Every SFX is generated at startup from primitives
(sin / square / triangle / pink-noise + ADSR envelopes + simple FM).
The result is cached and pygame.mixer plays it like any other Sound.

Three buses (music / sfx / voice) with independent volumes. If pygame.mixer
fails to initialize (rare), every play() becomes a no-op so callers never crash.
"""
import math
import random
import struct

try:
    import pygame
    _HAS_PYGAME = True
except ImportError:
    _HAS_PYGAME = False


SAMPLE_RATE = 44100
_INITIALIZED = False
_FAILED = False
_SOUNDS = {}
_BUS_VOLUMES = {"sfx": 0.7, "music": 0.5, "voice": 0.6}
_SOUND_BUS = {}
_LAST_PLAYED = {}
_MIN_REPLAY_INTERVAL = 0.04
_MUSIC_CHANNEL = None
_DUCK_FACTOR = 1.0
_DUCK_TARGET = 1.0
_DUCK_RECOVERY = 1.5

_CAPTIONS = {
    "draw":         "Card drawn",
    "place":        "Card placed",
    "flip":         "Card revealed",
    "pair":         "Pair!",
    "power_peek":   "Peek",
    "power_swap":   "Swap",
    "power_skip":   "Skip",
    "power_seen":   "Seen swap",
    "wrong_react":  "Wrong card",
    "react_open":   "Reaction window!",
    "declare":      "Declared",
    "win":          "Victory",
    "loss":         "Defeat",
    "hover":        "",
    "click":        "Click",
    "ui_open":      "Menu opened",
    "ui_close":     "Menu closed",
    "achievement":  "Achievement unlocked",
    "tutorial":     "",
    "shuffle":      "Shuffle",
}


def init():
    global _INITIALIZED, _FAILED, _MUSIC_CHANNEL
    if _INITIALIZED or _FAILED:
        return
    if not _HAS_PYGAME:
        _FAILED = True
        return
    try:
        pygame.mixer.pre_init(SAMPLE_RATE, -16, 2, 512)
        pygame.mixer.init()
        pygame.mixer.set_num_channels(16)
        _MUSIC_CHANNEL = pygame.mixer.Channel(0)
        _build_library()
        _INITIALIZED = True
    except (pygame.error, OSError):
        _FAILED = True


def _build_library():
    _SOUNDS["draw"] = _make_card_slide()
    _SOUNDS["place"] = _make_card_tap()
    _SOUNDS["flip"] = _make_card_flip()
    _SOUNDS["pair"] = _make_pair_chime()
    _SOUNDS["power_peek"] = _make_chime(660, 0.25, harmonics=[1, 2, 3], decay=0.15)
    _SOUNDS["power_swap"] = _make_chime(440, 0.30, harmonics=[1, 1.5, 2], decay=0.2)
    _SOUNDS["power_skip"] = _make_thud()
    _SOUNDS["power_seen"] = _make_chime(523, 0.35, harmonics=[1, 2, 4], decay=0.25)
    _SOUNDS["wrong_react"] = _make_buzzer()
    _SOUNDS["react_open"] = _make_react_open()
    _SOUNDS["declare"] = _make_declare_bell()
    _SOUNDS["win"] = _make_fanfare()
    _SOUNDS["loss"] = _make_loss_descent()
    _SOUNDS["hover"] = _make_hover()
    _SOUNDS["click"] = _make_click()
    _SOUNDS["ui_open"] = _make_drawer_open()
    _SOUNDS["ui_close"] = _make_drawer_close()
    _SOUNDS["achievement"] = _make_achievement()
    _SOUNDS["tutorial"] = _make_chime(550, 0.18, harmonics=[1, 2], decay=0.1)
    _SOUNDS["shuffle"] = _make_shuffle()

    for key in _SOUNDS:
        if key in ("hover", "click", "ui_open", "ui_close"):
            _SOUND_BUS[key] = "sfx"
        elif key == "achievement":
            _SOUND_BUS[key] = "voice"
        else:
            _SOUND_BUS[key] = "sfx"


def _to_sound(samples):
    """Convert a list of (left, right) float pairs in [-1, 1] to a pygame.Sound."""
    n = len(samples)
    buf = bytearray(n * 4)
    for i, (l, r) in enumerate(samples):
        li = max(-32767, min(32767, int(l * 32767)))
        ri = max(-32767, min(32767, int(r * 32767)))
        struct.pack_into("<hh", buf, i * 4, li, ri)
    return pygame.mixer.Sound(buffer=bytes(buf))


def _adsr(n, attack=0.01, decay=0.1, sustain=0.7, release=0.1):
    a = max(1, int(n * attack))
    d = max(1, int(n * decay))
    r = max(1, int(n * release))
    s = max(0, n - a - d - r)
    env = []
    for i in range(a):
        env.append(i / a)
    for i in range(d):
        t = i / d
        env.append(1.0 - (1.0 - sustain) * t)
    for _ in range(s):
        env.append(sustain)
    for i in range(r):
        t = i / r
        env.append(sustain * (1.0 - t))
    return env[:n]


def _stereo(samples, pan=0.0):
    pan = max(-1.0, min(1.0, pan))
    left = math.cos((pan + 1.0) * math.pi / 4)
    right = math.sin((pan + 1.0) * math.pi / 4)
    return [(s * left, s * right) for s in samples]


def _sine(freq, dur, amp=0.5):
    n = int(SAMPLE_RATE * dur)
    return [amp * math.sin(2 * math.pi * freq * i / SAMPLE_RATE) for i in range(n)]


def _square(freq, dur, amp=0.5):
    n = int(SAMPLE_RATE * dur)
    out = []
    period = SAMPLE_RATE / freq
    for i in range(n):
        out.append(amp if (i % period) < period / 2 else -amp)
    return out


def _triangle(freq, dur, amp=0.5):
    n = int(SAMPLE_RATE * dur)
    out = []
    period = SAMPLE_RATE / freq
    for i in range(n):
        phase = (i % period) / period
        out.append(amp * (4 * abs(phase - 0.5) - 1))
    return out


def _noise(dur, amp=0.5):
    n = int(SAMPLE_RATE * dur)
    return [amp * (2 * random.random() - 1) for _ in range(n)]


def _filter_lowpass(samples, cutoff_freq):
    rc = 1.0 / (2 * math.pi * cutoff_freq)
    dt = 1.0 / SAMPLE_RATE
    alpha = dt / (rc + dt)
    out = []
    prev = 0.0
    for s in samples:
        prev = prev + alpha * (s - prev)
        out.append(prev)
    return out


def _filter_highpass(samples, cutoff_freq):
    rc = 1.0 / (2 * math.pi * cutoff_freq)
    dt = 1.0 / SAMPLE_RATE
    alpha = rc / (rc + dt)
    out = []
    prev_in = 0.0
    prev_out = 0.0
    for s in samples:
        cur = alpha * (prev_out + s - prev_in)
        out.append(cur)
        prev_in = s
        prev_out = cur
    return out


def _add(a, b):
    if len(a) == len(b):
        return [a[i] + b[i] for i in range(len(a))]
    n = max(len(a), len(b))
    out = [0.0] * n
    for i, v in enumerate(a):
        out[i] += v
    for i, v in enumerate(b):
        out[i] += v
    return out


def _mul(samples, env):
    n = min(len(samples), len(env))
    return [samples[i] * env[i] for i in range(n)]


def _make_card_slide():
    n = int(SAMPLE_RATE * 0.15)
    samples = _filter_highpass(_noise(0.15, 0.6), 1200)
    samples = _filter_lowpass(samples, 6000)
    env = _adsr(n, 0.01, 0.04, 0.3, 0.05)
    samples = _mul(samples, env)
    return _to_sound(_stereo(samples, pan=-0.1))


def _make_card_tap():
    n = int(SAMPLE_RATE * 0.08)
    burst = _noise(0.08, 0.5)
    burst = _filter_lowpass(burst, 3000)
    burst = _filter_highpass(burst, 200)
    env = _adsr(n, 0.005, 0.02, 0.2, 0.04)
    samples = _mul(burst, env)
    woody = _sine(180, 0.08, 0.2)
    woody = _mul(woody, env)
    return _to_sound(_stereo(_add(samples, woody), pan=0.0))


def _make_card_flip():
    n = int(SAMPLE_RATE * 0.12)
    sweep = []
    for i in range(n):
        t = i / n
        f = 800 + 1400 * t
        sweep.append(0.4 * math.sin(2 * math.pi * f * i / SAMPLE_RATE))
    env = _adsr(n, 0.005, 0.05, 0.4, 0.07)
    samples = _mul(sweep, env)
    return _to_sound(_stereo(samples))


def _make_pair_chime():
    notes = []
    for f, t in [(523, 0.0), (659, 0.05), (784, 0.10)]:
        partial = _sine(f, 0.6, 0.35)
        partial = _add(partial, _sine(f * 2, 0.6, 0.18))
        partial = _add(partial, _sine(f * 3, 0.6, 0.10))
        env = _adsr(len(partial), 0.005, 0.4, 0.0, 0.4)
        partial = _mul(partial, env)
        delay = int(SAMPLE_RATE * t)
        padded = [0.0] * delay + partial
        notes.append(padded)
    n = max(len(x) for x in notes)
    mix = [0.0] * n
    for note in notes:
        for i, v in enumerate(note):
            mix[i] += v
    return _to_sound(_stereo(mix))


def _make_chime(freq, dur, harmonics=None, decay=0.2):
    if harmonics is None:
        harmonics = [1, 2, 3]
    base = _sine(freq, dur, 0.4)
    for h in harmonics[1:]:
        base = _add(base, _sine(freq * h, dur, 0.4 / h))
    env = _adsr(len(base), 0.005, decay, 0.0, decay)
    base = _mul(base, env)
    return _to_sound(_stereo(base))


def _make_thud():
    n = int(SAMPLE_RATE * 0.20)
    samples = []
    for i in range(n):
        t = i / n
        f = 120 - 60 * t
        samples.append(0.55 * math.sin(2 * math.pi * f * i / SAMPLE_RATE))
    env = _adsr(n, 0.005, 0.10, 0.0, 0.10)
    samples = _mul(samples, env)
    return _to_sound(_stereo(samples))


def _make_buzzer():
    n = int(SAMPLE_RATE * 0.45)
    base = _square(110, 0.45, 0.3)
    base = _add(base, _square(165, 0.45, 0.18))
    env = _adsr(n, 0.01, 0.05, 0.7, 0.30)
    samples = _mul(base, env)
    return _to_sound(_stereo(samples))


def _make_react_open():
    n = int(SAMPLE_RATE * 0.6)
    samples = []
    for i in range(n):
        t = i / n
        f = 440 + 660 * t
        samples.append(0.4 * math.sin(2 * math.pi * f * i / SAMPLE_RATE))
    env = _adsr(n, 0.02, 0.15, 0.5, 0.4)
    samples = _mul(samples, env)
    secondary = _sine(880, 0.6, 0.15)
    secondary = _mul(secondary, env)
    samples = _add(samples, secondary)
    return _to_sound(_stereo(samples))


def _make_declare_bell():
    notes = []
    for f, t, dur in [(659, 0.0, 1.4), (988, 0.06, 1.2), (1318, 0.12, 1.0)]:
        partial = _sine(f, dur, 0.35)
        partial = _add(partial, _sine(f * 2.7, dur, 0.10))
        partial = _add(partial, _sine(f * 5.4, dur, 0.05))
        env = _adsr(len(partial), 0.003, 0.6, 0.0, 0.7)
        partial = _mul(partial, env)
        delay = int(SAMPLE_RATE * t)
        notes.append([0.0] * delay + partial)
    n = max(len(x) for x in notes)
    mix = [0.0] * n
    for note in notes:
        for i, v in enumerate(note):
            mix[i] += v
    return _to_sound(_stereo(mix))


def _make_fanfare():
    sequence = [
        (523, 0.0, 0.2),
        (659, 0.18, 0.2),
        (784, 0.36, 0.4),
        (1047, 0.6, 0.8),
    ]
    notes = []
    for f, t, dur in sequence:
        partial = _sine(f, dur, 0.3)
        partial = _add(partial, _sine(f * 2, dur, 0.15))
        partial = _add(partial, _sine(f * 3, dur, 0.08))
        partial = _add(partial, _sine(f * 0.5, dur, 0.20))
        env = _adsr(len(partial), 0.01, 0.1, 0.6, 0.3)
        partial = _mul(partial, env)
        delay = int(SAMPLE_RATE * t)
        notes.append([0.0] * delay + partial)
    n = max(len(x) for x in notes)
    mix = [0.0] * n
    for note in notes:
        for i, v in enumerate(note):
            mix[i] += v
    return _to_sound(_stereo(mix))


def _make_loss_descent():
    sequence = [
        (440, 0.0, 0.3),
        (392, 0.28, 0.3),
        (330, 0.56, 0.4),
        (262, 0.84, 1.0),
    ]
    notes = []
    for f, t, dur in sequence:
        partial = _triangle(f, dur, 0.35)
        env = _adsr(len(partial), 0.02, 0.1, 0.5, 0.4)
        partial = _mul(partial, env)
        delay = int(SAMPLE_RATE * t)
        notes.append([0.0] * delay + partial)
    n = max(len(x) for x in notes)
    mix = [0.0] * n
    for note in notes:
        for i, v in enumerate(note):
            mix[i] += v
    return _to_sound(_stereo(mix))


def _make_hover():
    n = int(SAMPLE_RATE * 0.05)
    samples = _sine(2200, 0.05, 0.06)
    env = _adsr(n, 0.005, 0.02, 0.0, 0.025)
    samples = _mul(samples, env)
    return _to_sound(_stereo(samples))


def _make_click():
    n = int(SAMPLE_RATE * 0.08)
    samples = _noise(0.08, 0.45)
    samples = _filter_lowpass(samples, 5000)
    samples = _filter_highpass(samples, 1200)
    tone = _sine(880, 0.08, 0.2)
    samples = _add(samples, tone)
    env = _adsr(n, 0.002, 0.01, 0.3, 0.06)
    samples = _mul(samples, env)
    return _to_sound(_stereo(samples))


def _make_drawer_open():
    n = int(SAMPLE_RATE * 0.25)
    samples = _filter_lowpass(_noise(0.25, 0.4), 1000)
    samples = _filter_highpass(samples, 100)
    sweep = []
    for i in range(n):
        t = i / n
        f = 220 + 200 * t
        sweep.append(0.18 * math.sin(2 * math.pi * f * i / SAMPLE_RATE))
    samples = _add(samples, sweep)
    env = _adsr(n, 0.005, 0.05, 0.5, 0.15)
    samples = _mul(samples, env)
    return _to_sound(_stereo(samples))


def _make_drawer_close():
    n = int(SAMPLE_RATE * 0.18)
    samples = _filter_lowpass(_noise(0.18, 0.4), 800)
    sweep = []
    for i in range(n):
        t = i / n
        f = 420 - 220 * t
        sweep.append(0.22 * math.sin(2 * math.pi * f * i / SAMPLE_RATE))
    samples = _add(samples, sweep)
    env = _adsr(n, 0.003, 0.04, 0.4, 0.12)
    samples = _mul(samples, env)
    return _to_sound(_stereo(samples))


def _make_achievement():
    sequence = [
        (659, 0.0, 0.25),
        (784, 0.20, 0.25),
        (988, 0.40, 0.50),
    ]
    notes = []
    for f, t, dur in sequence:
        partial = _sine(f, dur, 0.4)
        partial = _add(partial, _sine(f * 2, dur, 0.18))
        partial = _add(partial, _sine(f * 3, dur, 0.08))
        env = _adsr(len(partial), 0.005, 0.2, 0.5, 0.3)
        partial = _mul(partial, env)
        delay = int(SAMPLE_RATE * t)
        notes.append([0.0] * delay + partial)
    n = max(len(x) for x in notes)
    mix = [0.0] * n
    for note in notes:
        for i, v in enumerate(note):
            mix[i] += v
    return _to_sound(_stereo(mix))


def _make_shuffle():
    n = int(SAMPLE_RATE * 1.6)
    samples = []
    rate = 18.0
    for i in range(n):
        t = i / SAMPLE_RATE
        burst_phase = (t * rate) % 1.0
        if burst_phase < 0.18:
            samples.append((random.random() * 2 - 1) * 0.5)
        else:
            samples.append((random.random() * 2 - 1) * 0.07)
    samples = _filter_highpass(samples, 1500)
    samples = _filter_lowpass(samples, 8000)
    env = _adsr(n, 0.05, 0.15, 0.7, 0.30)
    samples = _mul(samples, env)
    return _to_sound(_stereo(samples))


def _make_ambient_drone(duration_sec=20.0):
    n = int(SAMPLE_RATE * duration_sec)
    samples = [0.0] * n
    base_freqs = [55, 82.5, 110, 165]
    for f in base_freqs:
        amp = 0.10 + 0.05 * (1.0 / (f / 55.0))
        for i in range(n):
            t = i / SAMPLE_RATE
            mod = 0.5 + 0.5 * math.sin(2 * math.pi * 0.07 * t + f / 100)
            samples[i] += amp * mod * math.sin(2 * math.pi * f * t)
    samples = _filter_lowpass(samples, 1200)
    return _to_sound(_stereo(samples))


def play(key, volume=1.0, pan=0.0):
    """Play a SFX. Safe to call before init() or if init failed."""
    if not _INITIALIZED:
        return
    if key not in _SOUNDS:
        return
    import time
    now = time.monotonic()
    last = _LAST_PLAYED.get(key, 0.0)
    if now - last < _MIN_REPLAY_INTERVAL:
        return
    _LAST_PLAYED[key] = now
    bus = _SOUND_BUS.get(key, "sfx")
    bus_vol = _BUS_VOLUMES.get(bus, 1.0)
    final_vol = max(0.0, min(1.0, volume * bus_vol * _DUCK_FACTOR))
    sound = _SOUNDS[key]
    sound.set_volume(final_vol)
    try:
        sound.play()
    except pygame.error:
        pass


def caption(key) -> str:
    return _CAPTIONS.get(key, "")


def set_volume(bus, volume):
    if bus not in _BUS_VOLUMES:
        return
    _BUS_VOLUMES[bus] = max(0.0, min(1.0, volume))


def get_volume(bus):
    return _BUS_VOLUMES.get(bus, 0.0)


def duck(target=0.4):
    global _DUCK_TARGET
    _DUCK_TARGET = max(0.0, min(1.0, target))


def unduck():
    global _DUCK_TARGET
    _DUCK_TARGET = 1.0


def update(dt):
    global _DUCK_FACTOR
    if abs(_DUCK_FACTOR - _DUCK_TARGET) < 0.001:
        _DUCK_FACTOR = _DUCK_TARGET
        return
    direction = 1 if _DUCK_TARGET > _DUCK_FACTOR else -1
    _DUCK_FACTOR += direction * (dt * _DUCK_RECOVERY)
    if direction > 0:
        _DUCK_FACTOR = min(_DUCK_FACTOR, _DUCK_TARGET)
    else:
        _DUCK_FACTOR = max(_DUCK_FACTOR, _DUCK_TARGET)


def stop_all():
    if not _INITIALIZED:
        return
    pygame.mixer.stop()
