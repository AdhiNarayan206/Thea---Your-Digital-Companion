"""A tiny chiptune voice. numpy synthesis, no audio files."""

import numpy as np

SR = 44100
BEAT = 0.26

# An original eight-bar-ish phrase in C pentatonic. 0 = rest.
MELODY = [523.25, 659.25, 783.99, 659.25, 587.33, 659.25, 523.25, 0,
          587.33, 783.99, 880.00, 783.99, 659.25, 587.33, 523.25, 0]
BASS = [130.81, 130.81, 110.00, 110.00, 174.61, 174.61, 130.81, 130.81]


def _square(freq, dur, duty=0.5):
    n = int(SR * dur)
    t = np.arange(n) / SR
    phase = (t * freq) % 1.0
    return np.where(phase < duty, 1.0, -1.0)


def _triangle(freq, dur):
    n = int(SR * dur)
    t = np.arange(n) / SR
    return (2.0 / np.pi) * np.arcsin(np.sin(2 * np.pi * freq * t))


def _env(n, attack=0.008, release=0.06, sustain=0.75):
    a = max(1, int(SR * attack))
    r = max(1, int(SR * release))
    env = np.full(n, sustain, dtype=np.float64)
    a = min(a, n)
    env[:a] = np.linspace(0.0, 1.0, a, endpoint=False)
    r = min(r, n)
    env[n - r:] *= np.linspace(1.0, 0.0, r)
    return env


def _note(freq, dur, wave="square", gain=0.5):
    if freq <= 0:
        return np.zeros(int(SR * dur))
    sig = _square(freq, dur) if wave == "square" else _triangle(freq, dur)
    return sig * _env(len(sig)) * gain


def build_song():
    total = int(SR * BEAT * len(MELODY))
    out = np.zeros(total + SR // 4)

    for i, freq in enumerate(MELODY):
        buf = _note(freq, BEAT * 0.94, "square", 0.5)
        start = int(i * BEAT * SR)
        out[start:start + len(buf)] += buf

    bass_step = len(MELODY) / len(BASS)
    for i, freq in enumerate(BASS):
        buf = _note(freq, BEAT * bass_step * 0.92, "triangle", 0.42)
        start = int(i * bass_step * BEAT * SR)
        out[start:start + len(buf)] += buf

    peak = float(np.max(np.abs(out))) or 1.0
    return (out / peak * 0.22).astype(np.float32)


class Chiptune:
    def __init__(self):
        self._sd = None
        self._song = None
        self.enabled = True
        try:
            import sounddevice as sd

            self._sd = sd
        except Exception:
            self.enabled = False

    def _play(self, data):
        if not self.enabled or self._sd is None:
            return
        try:
            self._sd.stop()
            self._sd.play(data, SR, blocking=False)
        except Exception:
            self.enabled = False

    def sing(self):
        if self._song is None:
            self._song = build_song()
        self._play(self._song)

    def blip(self, freq=880.0, dur=0.07, gain=0.35):
        if not self.enabled:
            return
        try:
            self._play(_note(freq, dur, "square", gain).astype(np.float32))
        except Exception:
            pass

    def chime(self, freqs=(988.0, 1319.0), dur=0.09, gain=0.28):
        """Two quick notes in one buffer, so they are not cut off."""
        if not self.enabled:
            return
        try:
            parts = [_note(f, dur, "square", gain) for f in freqs]
            self._play(np.concatenate(parts).astype(np.float32))
        except Exception:
            pass

    def stop(self):
        if self._sd is not None:
            try:
                self._sd.stop()
            except Exception:
                pass
