"""Synthesised SFX. 16-bit PCM mono WAV."""
import numpy as np, wave, os
from paths import SFX_DIR

OUT = str(SFX_DIR)
os.makedirs(OUT, exist_ok=True)
SR = 22050


def write(name, sig):
    sig = np.clip(sig, -1, 1)
    pcm = (sig * 32000).astype("<i2")
    p = os.path.join(OUT, name + ".wav")
    with wave.open(p, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return p


def mix(*sigs):
    """Sum signals of differing lengths, zero-padded to the longest."""
    n = max(len(x) for x in sigs)
    out = np.zeros(n)
    for x in sigs:
        out[:len(x)] += x
    return out


def t(dur):
    return np.linspace(0, dur, int(SR * dur), endpoint=False)


def env(n, a=0.004, d=0.9, power=2.5):
    x = np.arange(n) / SR
    atk = np.clip(x / a, 0, 1)
    dec = np.exp(-power * x / d)
    return atk * dec


def tone(freq, dur, decay=None, kind="sine", detune=0.0):
    x = t(dur)
    if kind == "sine":
        w = np.sin(2 * np.pi * freq * x)
        if detune:
            w += 0.5 * np.sin(2 * np.pi * freq * (1 + detune) * x)
    elif kind == "tri":
        w = 2 * np.abs(2 * ((freq * x) % 1) - 1) - 1
    else:
        w = np.sign(np.sin(2 * np.pi * freq * x))
    return w * env(len(x), d=decay or dur)


def noise(dur, decay=None, lp=None):
    n = int(SR * dur)
    w = np.random.RandomState(7).randn(n)
    if lp:
        k = max(1, int(SR / lp))
        w = np.convolve(w, np.ones(k) / k, mode="same")
    return w * env(n, d=decay or dur)


def bell(freq, dur, parts=(1, 2.01, 3.03), amps=(1, .45, .2)):
    out = np.zeros(int(SR * dur))
    for p, a in zip(parts, amps):
        out += a * tone(freq * p, dur, decay=dur * (1.0 / p))
    return out / max(1e-9, np.max(np.abs(out)))


def arp(freqs, step=0.09, dur=0.30, kind="sine"):
    total = int(SR * (step * (len(freqs) - 1) + dur))
    out = np.zeros(total)
    for i, f in enumerate(freqs):
        s = int(SR * step * i)
        seg = bell(f, dur)
        out[s:s + len(seg)] += seg * 0.7
    return out / max(1e-9, np.max(np.abs(out)))


def build():
    made = {}
    # 1 click - UI
    made["click"] = write("click", mix(0.55 * noise(0.035, decay=0.012, lp=5000),
                                       0.35 * tone(1500, 0.035, decay=0.012)))
    # 2 reel tick
    made["reel"] = write("reel", mix(0.6 * tone(900, 0.045, decay=0.018, kind="tri"),
                                     0.3 * noise(0.03, decay=0.01, lp=7000)))
    # 3 card deal
    made["card"] = write("card", mix(0.85 * noise(0.10, decay=0.035, lp=3200),
                                     0.15 * tone(420, 0.06, decay=0.03)))
    # 4 chip clink
    ch = mix(0.5 * bell(2400, 0.16), 0.4 * noise(0.04, decay=0.014, lp=6000))
    made["chip"] = write("chip", ch)
    # 5 peg ping
    made["peg"] = write("peg", 0.7 * bell(1800, 0.07, parts=(1, 2.4), amps=(1, .3)))
    # 6 gem
    made["gem"] = write("gem", 0.8 * bell(1320, 0.26, parts=(1, 2.02, 3.9),
                                          amps=(1, .5, .25)))
    # 7 win - major arpeggio
    made["win"] = write("win", arp([523.25, 659.25, 783.99], 0.085, 0.34))
    # 8 bigwin - longer rising fanfare
    made["bigwin"] = write("bigwin",
                           arp([523.25, 659.25, 783.99, 1046.5, 1318.5],
                               0.085, 0.45))
    # 9 lose - falling minor
    made["lose"] = write("lose", arp([392.0, 311.13], 0.11, 0.32) * 0.85)
    # 10 bomb
    x = t(0.45)
    bm = mix(1.0 * noise(0.45, decay=0.13, lp=1400),
             0.7 * np.sin(2 * np.pi * (150 * np.exp(-6 * x)) * x)
             * env(len(x), d=0.16))
    made["bomb"] = write("bomb", bm / max(1e-9, np.max(np.abs(bm))))
    # 11 wheel tick
    made["tick"] = write("tick", mix(0.5 * tone(2200, 0.022, decay=0.008),
                                     0.4 * noise(0.018, decay=0.007, lp=9000)))
    # 12 cash out
    made["cash"] = write("cash", arp([659.25, 830.61, 987.77, 1318.5],
                                     0.07, 0.36))
    return made


SFX = ["click", "reel", "card", "chip", "peg", "gem",
       "win", "bigwin", "lose", "bomb", "tick", "cash"]

if __name__ == "__main__":
    m = build()
    tot = sum(os.path.getsize(p) for p in m.values())
    for n in SFX:
        print(f"  {n:<7} {os.path.getsize(m[n]) / 1024:6.1f} KB")
    print(f"total {tot / 1024:.0f} KB")
