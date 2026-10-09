"""Videoya özel, telifsiz yumuşak piyano parçası (MIDI -> FluidSynth).

66 BPM, 4/4 — bir ölçü = 3.636 sn. Her fotoğraf geçişi bir ölçü başına denk gelir:
  ölçü 1-2   : açılış (∞ ve isimler)
  ölçü 3-18  : 16 fotoğraf (her fotoğraf bir ölçü)
  ölçü 19-21 : kapanış (sonsuzluk döngüsü), son akor çınlayarak biter

Gerekenler: pip install mido ; apt install fluidsynth fluid-soundfont-gm
Kullanım:   python3 scripts/piyano.py assets/music/piyano.wav
"""

import os
import subprocess
import sys
import tempfile

import mido
import numpy as np

BPM = 66
TPB = 480  # ticks per beat
BAR_TICKS = 4 * TPB
SOUNDFONT = "/usr/share/sounds/sf2/FluidR3_GM.sf2"
TOTAL_SECONDS = 80.0

rng = np.random.default_rng(12)  # 12. yıl

# --- harmony ------------------------------------------------------------------
D, E, Fs, G, A, B, Cs = 50, 52, 54, 55, 57, 59, 49  # octave-3 roots (C#3 = 49)
MAJ = [0, 7, 12, 16, 19, 16, 12, 7]
MIN = [0, 7, 12, 15, 19, 15, 12, 7]
MAJ7 = [0, 7, 11, 16, 19, 16, 11, 7]
SUS = [0, 7, 12, 17, 19, 16, 12, 7]

# bar -> (bass note, arpeggio root, pattern, pad voicing)
chords = {
    1: (G - 12, G, MAJ7, [55, 59, 62, 66]),
    2: (A - 12, A, SUS, [57, 61, 64, 69]),
    3: (D - 12, D, MAJ, [57, 62, 66, 69]),
    4: (Cs, A, MAJ, [57, 61, 64, 69]),
    5: (B - 12, B, MIN, [59, 62, 66, 71]),
    6: (G - 12, G, MAJ, [55, 59, 62, 67]),
    7: (D - 12, D, MAJ, [57, 62, 66, 69]),
    8: (A - 12, A, MAJ, [57, 61, 64, 69]),
    9: (G - 12, G, MAJ, [55, 59, 62, 67]),
    10: (A - 12, A, MAJ, [57, 61, 64, 69]),
    11: (B - 12, B, MIN, [59, 62, 66, 71]),
    12: (G - 12, G, MAJ, [55, 59, 62, 67]),
    13: (D - 12, D, MAJ, [57, 62, 66, 69]),
    14: (A - 12, A, MAJ, [57, 61, 64, 69]),
    15: (G - 12, G, MAJ, [55, 59, 62, 67]),
    16: (A - 12, A, MAJ, [57, 61, 64, 69]),
    17: (B - 12, B, MIN, [59, 62, 66, 71]),
    18: (A - 12, A, MAJ, [57, 61, 64, 69]),
    19: (G - 12, G, MAJ7, [55, 59, 62, 66]),
    20: (A - 12, A, SUS, [57, 61, 64, 69]),
}

# bar -> [(beat (1-based), length in beats, midi)]
melody = {
    3: [(1, 2, 78), (3, 1, 76), (4, 1, 74)],
    4: [(1, 3, 76), (4, 1, 73)],
    5: [(1, 1.5, 74), (2.5, 0.5, 73), (3, 2, 71)],
    6: [(1, 2, 67), (3, 1, 69), (4, 1, 71)],
    7: [(1, 1.5, 81), (2.5, 0.5, 78), (3, 1, 81), (4, 1, 83)],
    8: [(1, 2, 81), (3, 2, 76)],
    9: [(1, 1, 74), (2, 1, 76), (3, 1, 78), (4, 1, 79)],
    10: [(1, 2, 78), (3, 2, 76)],
    11: [(1, 1.5, 78), (2.5, 0.5, 76), (3, 1, 74), (4, 1, 78)],
    12: [(1, 2, 83), (3, 1, 81), (4, 1, 79)],
    13: [(1, 1.5, 78), (2.5, 0.5, 76), (3, 1, 74), (4, 1, 69)],
    14: [(1, 2, 73), (3, 2, 76)],
    15: [(1, 1.5, 83), (2.5, 0.5, 81), (3, 1, 79), (4, 1, 78)],
    16: [(1, 1, 76), (2, 1, 78), (3, 1, 79), (4, 1, 81)],
    17: [(1, 2, 78), (3, 1, 74), (4, 1, 78)],
    18: [(1, 2, 76), (3, 1, 73), (4, 1, 76)],
    19: [(1, 2, 74), (3, 2, 71)],
    20: [(1, 2, 73), (3, 2, 76)],
}


def dyn(bar):
    """Base velocity per section: quiet open, gradual swell, calm close."""
    if bar <= 2:
        return 42
    if bar <= 6:
        return 52
    if bar <= 10:
        return 60
    if bar <= 14:
        return 66
    if bar <= 18:
        return 74
    return 58


def bar_tick(bar, beat=1.0):
    return int((bar - 1) * BAR_TICKS + (beat - 1) * TPB)


def jitter(sd=6):
    return int(rng.normal(0, sd))


def vel(v, sd=4):
    return int(np.clip(v + rng.normal(0, sd), 1, 127))


def build_midi(path):
    events = []  # (tick, order, channel, message)

    def note(ch, tick, length, midi, velocity):
        tick = max(0, tick)
        events.append((tick, 1, mido.Message("note_on", channel=ch, note=midi, velocity=velocity)))
        events.append((tick + max(1, length), 0, mido.Message("note_off", channel=ch, note=midi, velocity=0)))

    def cc(ch, tick, control, value):
        events.append((max(0, tick), 0, mido.Message("control_change", channel=ch, control=control, value=int(value))))

    # channel 0: grand piano, channel 1: soft strings pad
    events.append((0, 0, mido.Message("program_change", channel=0, program=0)))
    events.append((0, 0, mido.Message("program_change", channel=1, program=49)))
    cc(0, 0, 7, 112)
    cc(0, 0, 91, 70)  # reverb send
    cc(0, 0, 93, 10)
    cc(1, 0, 7, 70)
    cc(1, 0, 91, 100)
    cc(1, 0, 11, 0)

    for bar, (bass, root, pat, pad) in chords.items():
        t0 = bar_tick(bar)
        v = dyn(bar)
        # sustain pedal: lift just before the bar, press just after the downbeat
        cc(0, t0 - 12, 64, 0)
        cc(0, t0 + 18, 64, 127)
        note(0, t0 + jitter(3), BAR_TICKS, bass, vel(v - 4))
        if bar == 1:
            for i, iv in enumerate(pat[:4]):
                note(0, t0 + i * TPB + jitter(), BAR_TICKS - i * TPB, root + iv, vel(v - 8))
        else:
            for i, iv in enumerate(pat):
                if i == 0:
                    continue  # bass already sounds the root on the downbeat
                st = t0 + i * (TPB // 2) + jitter()
                note(0, st, BAR_TICKS - i * (TPB // 2), root + iv, vel(v - 12 + (4 if i == 4 else 0)))
        # string pad from the second phrase on, swelling into the climax
        if bar >= 7:
            for m in pad:
                note(1, t0 + 30, BAR_TICKS - 40, m, 50)

    # pad expression envelope (CC11) per bar
    pad_level = {b: lv for b, lv in zip(range(7, 21), [30, 38, 44, 48, 54, 58, 62, 64, 74, 80, 84, 86, 64, 50])}
    for bar, lv in pad_level.items():
        t0 = bar_tick(bar)
        prev = pad_level.get(bar - 1, 0)
        for s in range(8):
            cc(1, t0 + s * BAR_TICKS // 8, 11, prev + (lv - prev) * (s + 1) / 8)

    # intro sparkles
    note(0, bar_tick(1, 3), 3 * TPB, 86, 34)
    note(0, bar_tick(2, 3), 3 * TPB, 88, 32)

    for bar, notes in melody.items():
        v = dyn(bar) + 14
        for beat, length, m in notes:
            st = bar_tick(bar, beat) + jitter(8)
            ln = int(length * TPB) - 20
            accent = 6 if beat == 1 else 0
            note(0, st, ln, m, vel(v + accent))
            if 15 <= bar <= 18:  # climax: octave doubling underneath
                note(0, st + 6, ln, m - 12, vel(v - 18))

    # final rolled chord — sonsuzluğa
    t21 = bar_tick(21)
    cc(0, t21 - 12, 64, 0)
    cc(0, t21 + 18, 64, 127)
    final = [(26, 52), (38, 56), (45, 50), (50, 54), (54, 50), (57, 52), (62, 56), (66, 58), (69, 60), (74, 66)]
    for i, (m, v) in enumerate(final):
        note(0, t21 + i * 22, 6 * TPB, m, v)
    for m in [50, 57, 62, 66]:
        note(1, t21 + 30, 6 * TPB, m, 46)
    for s in range(12):
        cc(1, t21 + s * TPB // 2, 11, 60 * (1 - (s + 1) / 12))
    note(0, bar_tick(21, 3), 4 * TPB, 86, 36)
    note(0, bar_tick(21, 4), 4 * TPB, 81, 30)

    mid = mido.MidiFile(ticks_per_beat=TPB)
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(BPM), time=0))
    last = 0
    for tick, _, msg in sorted(events, key=lambda e: (e[0], e[1])):
        track.append(msg.copy(time=tick - last))
        last = tick
    mid.save(path)


def main(out_path):
    with tempfile.TemporaryDirectory() as tmp:
        mid_path = os.path.join(tmp, "piyano.mid")
        raw = os.path.join(tmp, "raw.wav")
        build_midi(mid_path)
        subprocess.run(
            ["fluidsynth", "-ni", "-q", "-r", "48000", "-g", "0.6",
             "-o", "synth.reverb.room-size=0.75", "-o", "synth.reverb.width=0.9",
             "-o", "synth.reverb.damp=0.35", "-o", "synth.reverb.level=0.7",
             "-F", raw, SOUNDFONT, mid_path],
            check=True,
        )
        # trim/pad to the video length with a gentle tail fade
        shaped = os.path.join(tmp, "shaped.wav")
        subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", raw,
             "-af", f"apad,atrim=0:{TOTAL_SECONDS},afade=t=out:st={TOTAL_SECONDS - 3.5}:d=3.5",
             "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", shaped],
            check=True,
        )
        # static gain to about -16 LUFS (no dynamic pumping), peak-limited
        stats = subprocess.run(
            ["ffmpeg", "-hide_banner", "-i", shaped, "-af", "ebur128=framelog=quiet", "-f", "null", "-"],
            capture_output=True, text=True, check=True,
        ).stderr
        lufs = float(stats.split("Integrated loudness:")[1].split("I:")[1].split("LUFS")[0])
        gain = -16.0 - lufs
        subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", shaped,
             "-af", f"volume={gain:.2f}dB,alimiter=limit=0.84:level=false",
             "-c:a", "pcm_s16le", out_path],
            check=True,
        )
        print(f"measured {lufs:.1f} LUFS, applied {gain:+.1f} dB")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "assets/music/piyano.wav")
