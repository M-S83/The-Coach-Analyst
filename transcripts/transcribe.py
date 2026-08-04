#!/usr/bin/env python3
"""Fixed-window Whisper transcription (full coverage) for quiet pitch-side audio."""
import sys, os, json, time, re
import numpy as np
import soundfile as sf
import sherpa_onnx

SP = os.path.dirname(os.path.abspath(__file__))
MODEL = os.environ.get("WMODEL", "turbo")
MDIR = os.path.join(SP, "models", f"sherpa-onnx-whisper-{MODEL}")
SR = 16000
WIN = 28.0
STRIDE = float(os.environ.get("STRIDE", 22.0))

HALLU = re.compile(r"^(thank you\.?|thanks for watching.*|you\.?|bye\.?|\.|"
                   r"subtitles by.*|subs by.*|amara\.org.*|\[.*\])$", re.I)


def build_recognizer(threads=4):
    return sherpa_onnx.OfflineRecognizer.from_whisper(
        encoder=os.path.join(MDIR, f"{MODEL}-encoder.int8.onnx"),
        decoder=os.path.join(MDIR, f"{MODEL}-decoder.int8.onnx"),
        tokens=os.path.join(MDIR, f"{MODEL}-tokens.txt"),
        language="en", task="transcribe",
        num_threads=threads, decoding_method="greedy_search",
        tail_paddings=2000,
    )


def collapse_repeats(text, max_rep=1):
    """Whisper loops on noise; collapse runs of an identical phrase."""
    parts = re.split(r"(?<=[.!?])\s+", text)
    out, prev, n = [], None, 0
    for p in parts:
        key = p.strip().lower()
        if key and key == prev:
            n += 1
            if n >= max_rep:
                continue
        else:
            prev, n = key, 0
        out.append(p)
    text = " ".join(out)
    words = text.split()
    out, i = [], 0
    while i < len(words):
        out.append(words[i])
        j = i
        while j + 1 < len(words) and words[j + 1].lower() == words[i].lower():
            j += 1
        if j - i >= 2:
            i = j + 1
        else:
            i += 1
    return " ".join(out)


def dedup_overlap(prev, cur, max_words=25):
    """Trim words at the head of `cur` that repeat the tail of `prev`."""
    if not prev or not cur:
        return cur
    pw, cw = prev.split(), cur.split()
    norm = lambda ws: [re.sub(r"[^\w']", "", w).lower() for w in ws]
    pn, cn = norm(pw), norm(cw)
    best = 0
    for k in range(min(max_words, len(pn), len(cn)), 2, -1):
        if pn[-k:] == cn[:k]:
            best = k
            break
    return " ".join(cw[best:])


def hms(t):
    t = max(0.0, t)
    return f"{int(t // 3600):02d}:{int(t % 3600 // 60):02d}:{int(t % 60):02d}"


def main(wav_path, out_prefix, label):
    x, sr = sf.read(wav_path, dtype="float32")
    if x.ndim > 1:
        x = x.mean(axis=1)
    dur = len(x) / sr
    rec = build_recognizer()
    print(f"[{label}] {dur/60:.2f} min", flush=True)

    segs, t0, prev_text = [], time.time(), ""
    start = 0.0
    while start < dur:
        a, b = int(start * sr), int(min(dur, start + WIN) * sr)
        chunk = x[a:b]
        if len(chunk) < int(0.4 * sr):
            break
        rms = float(np.sqrt((chunk ** 2).mean()))
        st = rec.create_stream()
        st.accept_waveform(sr, chunk)
        rec.decode_stream(st)
        text = collapse_repeats(st.result.text.strip())
        text = dedup_overlap(prev_text, text)
        if text and not HALLU.match(text.strip()):
            segs.append({"start": start, "end": min(dur, start + WIN),
                         "rms": rms, "text": text})
            prev_text = text
            print(f"[{hms(start)}] {text}", flush=True)
        start += STRIDE
    with open(out_prefix + ".json", "w") as f:
        json.dump({"file": os.path.basename(wav_path), "label": label,
                   "duration_s": dur, "segments": segs}, f, indent=1)
    with open(out_prefix + ".txt", "w") as f:
        f.write(f"# {label}\n# source: {os.path.basename(wav_path)}  "
                f"duration {hms(dur)}\n\n")
        for s in segs:
            f.write(f"[{hms(s['start'])}] {s['text']}\n\n")
    print(f"[{label}] done in {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
