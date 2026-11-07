# Fleet Signal Analysis — initial executable engine

Offline analysis of **authorized PCM WAV** recordings for fleet contacts. Works on Linux with Python standard library, no external dependencies.

## Usage

```bash
python3 -m fleet_apps.signal_analysis recording.wav --kind radio \
  --source-ref sensor://aurora/receiver-01 --output report.json
python3 -m fleet_apps.signal_reports report-a.json report-b.json
python3 -m unittest tests.test_signal_analysis -v
```

## Current capabilities

- WAV validation and recording-size/time limits.
- RMS amplitude, peak level, DC offset, zero-crossing rate.
- Approximate dominant frequency peaks and silence detection.
- SHA-256 recording fingerprint and source reference.
- Comparison of two or more reports; no unsupported sender identification.
- JSON report format for future chat/map integration.

## Important limitations

No real-time receiver, sensor adapters, RF tuning, transmission interception, decoding, decryption, AI worker dispatcher, or UI integration yet. Analysis is approximate and does not establish origin or authenticity. All reports default to `source_verified=false`. Hyperspace transmission remains a simulation label only.

Next: authenticated ingestion API, worker processing queue, artifact retention, safe live signal adapters, event stream to LibreChat/map, audit logs and explicit provenance verification. Do not capture private third-party communications without authorization.
