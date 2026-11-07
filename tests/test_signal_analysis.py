import math
import struct
import tempfile
import unittest
import wave
from pathlib import Path
from fleet_apps.signal_analysis import analyze_wav
from fleet_apps.signal_reports import compare_reports


class SignalAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "tone.wav"
        rate = 8000
        samples = [int(14000 * math.sin(2 * math.pi * 440 * i / rate))
                   for i in range(rate)]
        with wave.open(str(self.path), "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(rate)
            wav.writeframes(struct.pack("<" + "h" * len(samples), *samples))

    def tearDown(self):
        self.tmp.cleanup()

    def test_signal_metrics(self):
        result = analyze_wav(self.path, kind="radio", source_ref="authorized:sample")
        self.assertAlmostEqual(result["duration_seconds"], 1, places=2)
        self.assertGreater(result["rms"], 0.2)
        self.assertTrue(any(abs(x["frequency_hz"] - 440) < 40 for x in result["spectral_peaks"]))
        self.assertFalse(result["source_verified"])

    def test_missing_provenance(self):
        with self.assertRaises(ValueError):
            analyze_wav(self.path, source_ref="")

    def test_compare_does_not_assert_identity(self):
        a = analyze_wav(self.path, source_ref="ship:A")
        b = analyze_wav(self.path, source_ref="ship:B")
        result = compare_reports([a, b])
        self.assertFalse(result["comparisons"][0]["same_sender_verified"])


if __name__ == "__main__":
    unittest.main()
