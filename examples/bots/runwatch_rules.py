#!/usr/bin/env python3
"""runwatch rules shim — deterministic anomaly checks (no LLM involved).

Usage: python runwatch_rules.py "file_added(runs/7/metrics.json)"
Prints exact deltas vs. the rolling baseline; the bot quotes these verbatim.
"""

import json
import math
import statistics
import sys
from pathlib import Path

SIGMA_LIMIT = 3.0
THRESHOLD_SHIFT_LIMIT = 0.15
BASELINE_FILE = Path(".gitbot/state/baselines.json")


def extract_path(trigger: str) -> Path:
    return Path(trigger[trigger.index("(") + 1 : -1])


def load_metrics(path: Path) -> dict:
    data = json.loads(path.read_text())
    flat = {}
    for k, v in data.get("metrics", data).items():
        if isinstance(v, (int, float)) and isinstance(v, float) and math.isnan(v):
            flat[k] = None
        elif isinstance(v, (int, float)):
            flat[k] = float(v)
    return flat


def main() -> None:
    metrics_path = extract_path(sys.argv[1]) if len(sys.argv) > 1 else None
    if not metrics_path or not metrics_path.exists():
        print("SKIP: no metrics file")
        return

    current = load_metrics(metrics_path)
    baseline = json.loads(BASELINE_FILE.read_text()) if BASELINE_FILE.exists() else {}
    anomalies = []

    for metric, value in current.items():
        if value is None:
            anomalies.append(f"{metric}: NaN in new run")
            continue
        hist = baseline.get(metric, [])
        if len(hist) < 5:
            continue  # not enough history
        mean, std = statistics.mean(hist), (statistics.stdev(hist) or 1e-9)
        z = (value - mean) / std
        if abs(z) > SIGMA_LIMIT:
            anomalies.append(f"{metric}: {value:.4f} is {z:+.1f}σ vs baseline mean {mean:.4f}")
        if metric == "threshold" and abs(value - mean) > THRESHOLD_SHIFT_LIMIT:
            anomalies.append(f"threshold shifted {value - mean:+.3f} (limit ±{THRESHOLD_SHIFT_LIMIT})")

    missing = set(baseline) - set(current)
    if missing:
        anomalies.append(f"missing keys: {sorted(missing)}")

    print("ANOMALIES:" if anomalies else "CLEAN:")
    for a in anomalies or ["all metrics within 3σ of baseline"]:
        print(f"- {a}")

    # fold this run into the rolling baseline (last 20)
    for metric, value in current.items():
        if value is not None:
            baseline.setdefault(metric, []).append(value)
            baseline[metric] = baseline[metric][-20:]
    BASELINE_FILE.parent.mkdir(parents=True, exist_ok=True)
    BASELINE_FILE.write_text(json.dumps(baseline, indent=2))


if __name__ == "__main__":
    main()
