"""Offline signal analysis for authorized recordings, no RF interception.

Input: mono/stereo PCM WAV (8/16/32-bit integer), sampled by an external
authorized source. Spectral peaks use Goertzel scanning, stdlib only.
"""
import argparse
import hashlib
import json
import math
import struct
import wave
from pathlib import Path

MAX_BYTES = 32 * 1024 * 1024
MAX_SECONDS = 120
MAX_SAMPLES = 48000
KINDS = {"radio", "network", "unknown", "hyperspace_simulation"}


def _read_wav(path):
    path = Path(path)
    if path.stat().st_size > MAX_BYTES:
        raise ValueError("File too large")
    with wave.open(str(path), "rb") as wav:
        channels, width, rate = wav.getnchannels(), wav.getsampwidth(), wav.getframerate()
        count = wav.getnframes()
        if channels not in (1, 2) or width not in (1, 2, 4) or rate < 100 or rate > 192000:
            raise ValueError("Unsupported PCM format")
        if count / rate > MAX_SECONDS:
            raise ValueError("Recording too long")
        raw = wav.readframes(count)
    if width == 1:
        values = [float(v - 128) / 128 for v in raw]
    else:
        code = {2: "h", 4: "i"}[width]
        size = len(raw) // width
        values = [float(v) / (2 ** (width * 8 - 1))
                  for v in struct.unpack("<" + code * size, raw)]
    mono = values[::channels] if channels == 1 else [
        (values[i] + values[i + 1]) / 2 for i in range(0, len(values), 2)]
    if len(mono) > MAX_SAMPLES:
        step = math.ceil(len(mono) / MAX_SAMPLES)
        mono = mono[::step]
        effective_rate = rate / step
    else:
        effective_rate = float(rate)
    return mono, rate, effective_rate, count, hashlib.sha256(raw).hexdigest()


def _peak_frequencies(samples, rate, bins=120):
    n = min(len(samples), 4096)
    if n < 8:
        return []
    window = samples[:n]
    nyquist = rate / 2
    powers = []
    for i in range(1, bins + 1):
        freq = nyquist * i / (bins + 1)
        omega = 2 * math.pi * freq / rate
        coeff = 2 * math.cos(omega)
        prev = prev2 = 0.0
        for sample in window:
            current = sample + coeff * prev - prev2
            prev2, prev = prev, current
        power = max(0.0, prev2 * prev2 + prev * prev - coeff * prev * prev2)
        powers.append((freq, power))
    powers.sort(key=lambda pair: pair[1], reverse=True)
    return [{"frequency_hz": round(f, 2), "relative_power": round(p, 4)}
            for f, p in powers[:5]]


def analyze_wav(path, *, kind="unknown", source_ref=None):
    if kind not in KINDS:
        raise ValueError("Invalid signal kind")
    if not isinstance(source_ref, str) or not source_ref.strip() or len(source_ref) > 512:
        raise ValueError("A source reference is required")
    samples, original_rate, effective_rate, count, digest = _read_wav(path)
    if not samples:
        raise ValueError("Empty recording")
    rms = math.sqrt(sum(s * s for s in samples) / len(samples))
    peak = max(abs(s) for s in samples)
    mean = sum(samples) / len(samples)
    crossings = sum((a >= 0) != (b >= 0) for a, b in zip(samples, samples[1:]))
    return {
        "schema_version": 1,
        "signal_kind": kind,
        "source_ref": source_ref,
        "recording_sha256": digest,
        "source_verified": False,
        "sample_rate_hz": original_rate,
        "analyzed_rate_hz": round(effective_rate, 2),
        "duration_seconds": round(count / original_rate, 3),
        "rms": round(rms, 6),
        "peak_amplitude": round(peak, 6),
        "dc_offset": round(mean, 6),
        "zero_crossing_rate": round(crossings / max(1, len(samples) - 1), 6),
        "spectral_peaks": _peak_frequencies(samples, effective_rate),
        "silence_detected": rms < 0.001,
        "caveats": [
            "Frequency peaks are approximate and based on a short sampled window.",
            "This analysis does not identify a sender, decrypt traffic, or establish an alliance.",
            "Hyperspace simulation is not evidence of a physical hyperspace signal."
        ],
    }


def main():
    p = argparse.ArgumentParser(description="Offline fleet signal analyzer")
    p.add_argument("wav")
    p.add_argument("--kind", choices=sorted(KINDS), default="unknown")
    p.add_argument("--source-ref", required=True)
    p.add_argument("--output", help="Optional JSON output file")
    args = p.parse_args()
    result = analyze_wav(args.wav, kind=args.kind, source_ref=args.source_ref)
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
