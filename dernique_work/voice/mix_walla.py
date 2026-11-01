"""Layer the individual TTS lines into two subway walla tracks (8s each).

A: commuters complaining about the stale, musty air.
B: commuters reacting to a pleasant scent.
Each track = foreground lines at staggered offsets + a muffled murmur bed made
from the same lines (pitch-shifted, low-passed, delayed) + a low train rumble.
"""
import subprocess
from pathlib import Path

D = Path(__file__).resolve().parent
LEN = 8.0

TRACKS = {
    "A_불쾌_웅성": [  # (file, start sec, gain, distance 0=near 1=far)
        ("A1_남_이게무슨냄새야", 0.3, 0.9, 0.2),
        ("A2_여_숨막힌다", 1.2, 0.8, 0.4),
        ("A4_여_땀냄새심하다", 2.0, 0.85, 0.1),
        ("A3_남_사람너무많네", 3.0, 0.7, 0.6),
        ("A5_남_에어컨좀", 4.0, 0.75, 0.5),
        ("A6_여_답답해빨리내리고싶다", 5.4, 0.8, 0.3),
    ],
    "B_향기_반응": [
        ("B1_여_무슨냄새지", 0.3, 0.9, 0.1),
        ("B2_남_향기좋다", 1.1, 0.85, 0.3),
        ("B3_여_무슨향수야", 2.2, 0.85, 0.2),
        ("B6_남_뭐지이향", 3.0, 0.7, 0.6),
        ("B4_남_좋은냄새난다", 4.1, 0.75, 0.5),
        ("B5_여_어디서나는거지", 5.0, 0.8, 0.4),
    ],
}
BED_PITCH = [0.92, 1.06, 0.97, 1.1, 0.88, 1.02]


def build(name, lines):
    args, fc, mix = [], [], []
    for i, (f, start, gain, dist) in enumerate(lines):
        args += ["-i", str(D / "trim" / f"{f}.wav")]
        lp = int(9000 - dist * 6000)
        fc.append(
            f"[{i}:a]lowpass=f={lp},volume={gain * (1 - dist * 0.45):.2f},"
            f"adelay={int(start * 1000)}|{int(start * 1000)},apad=whole_dur={LEN}[f{i}]"
        )
        mix.append(f"[f{i}]")
    # muffled murmur bed: every line again, re-pitched, far away, looped across the track
    n = len(lines)
    for i, (f, *_rest) in enumerate(lines):
        p = BED_PITCH[i % len(BED_PITCH)]
        for k, off in enumerate((0.0, 2.6, 5.1)):
            d = int((off + i * 0.37) * 1000) % 6000
            fc.append(
                f"[{i}:a]asetrate=44100*{p},aresample=44100,lowpass=f=1400,highpass=f=180,"
                f"volume=0.16,adelay={d}|{d},apad=whole_dur={LEN}[b{i}_{k}]"
            )
            mix.append(f"[b{i}_{k}]")
    # train rumble
    args += ["-f", "lavfi", "-t", str(LEN), "-i", "anoisesrc=color=brown:amplitude=0.5:sample_rate=44100"]
    fc.append(f"[{n}:a]lowpass=f=160,volume=0.35,aformat=channel_layouts=stereo[rum]")
    mix.append("[rum]")
    fc.append(
        f"{''.join(mix)}amix=inputs={len(mix)}:normalize=0,"
        f"aecho=0.8:0.6:40|70:0.25|0.15,atrim=0:{LEN},"
        f"afade=t=in:d=0.4,afade=t=out:st={LEN - 0.6}:d=0.6,"
        f"loudnorm=I=-20:TP=-2:LRA=11[out]"
    )
    out = D / f"DERNIQUE_지하철웅성_{name}.wav"
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", *args, "-filter_complex", ";".join(fc),
                    "-map", "[out]", "-ar", "48000", str(out)], check=True)
    print("wrote", out.name)


for name, lines in TRACKS.items():
    build(name, lines)
