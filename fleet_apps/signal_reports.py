"""Compare authorized signal analysis reports without assuming shared identity."""
import json
import math
from pathlib import Path


def compare_reports(reports):
    if len(reports) < 2:
        raise ValueError("At least two reports required")
    for report in reports:
        if not isinstance(report, dict) or report.get("schema_version") != 1:
            raise ValueError("Unsupported report")
    base = reports[0]
    results = []
    for report in reports[1:]:
        a = base.get("spectral_peaks", [])
        b = report.get("spectral_peaks", [])
        if not a or not b:
            similarity = None
        else:
            f1, f2 = a[0]["frequency_hz"], b[0]["frequency_hz"]
            similarity = round(max(0.0, 1.0 - abs(f1 - f2) / max(f1, f2, 1.0)), 4)
        results.append({
            "source_a": base["source_ref"],
            "source_b": report["source_ref"],
            "dominant_frequency_similarity": similarity,
            "same_sender_verified": False,
        })
    return {"comparisons": results,
            "warning": "Similar spectra do not prove a shared sender or verified alliance."}


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("reports", nargs="+")
    args = p.parse_args()
    data = [json.loads(Path(path).read_text(encoding="utf-8")) for path in args.reports]
    print(json.dumps(compare_reports(data), indent=2))


if __name__ == "__main__":
    main()
