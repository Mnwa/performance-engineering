#!/usr/bin/env python3
"""Analyze independent paired measurements; not a benchmark collector.

Geometric mean of per-pair speedups + paired percentile-bootstrap interval.
Exit codes: 0 all PASS; 1 a REGRESSION; 2 invalid input; 3 INCONCLUSIVE.
No dependencies beyond Python 3.10+ standard library.
"""
from __future__ import annotations
import argparse
import json
import math
import random
import sys
from pathlib import Path
from typing import Any


def positive_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a positive finite number")
    try:
        number = float(value)
    except (ValueError, OverflowError) as exc:
        raise ValueError(f"{label} is not a finite representable number") from exc
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"{label} must be a positive finite number")
    return number


def no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle, object_pairs_hook=no_duplicate_keys)
    if not isinstance(data, dict):
        raise ValueError("input must be a JSON object")
    return data


def quantile(sorted_values: list[float], probability: float) -> float:
    position = (len(sorted_values) - 1) * probability
    lo = math.floor(position)
    hi = math.ceil(position)
    return sorted_values[lo] + (sorted_values[hi] - sorted_values[lo]) * (position - lo)


def finite_exp(value: float) -> float:
    try:
        result = math.exp(value)
    except OverflowError as exc:
        raise ValueError("normalized speedup exceeds floating-point range") from exc
    if not math.isfinite(result) or result <= 0:
        raise ValueError("normalized speedup is outside positive floating-point range")
    return result


def analyze(data: dict[str, Any], *, minimum_speedup: float = 0.95,
            confidence: float = 0.95, bootstrap: int = 10000,
            min_pairs: int = 10, seed: int = 20260905,
            bonferroni: bool = False) -> dict[str, Any]:
    minimum_speedup = positive_number(minimum_speedup, "minimum_speedup")
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not 0 < confidence < 1:
        raise ValueError("confidence must be between zero and one")
    if isinstance(bootstrap, bool) or not isinstance(bootstrap, int) or bootstrap < 1000:
        raise ValueError("bootstrap must be an integer >= 1000")
    if isinstance(min_pairs, bool) or not isinstance(min_pairs, int) or min_pairs < 2:
        raise ValueError("min_pairs must be an integer >= 2")
    if not isinstance(data, dict) or type(data.get("schema_version")) is not int or data["schema_version"] != 1:
        raise ValueError("schema_version must be integer 1")
    metric = data.get("metric")
    if metric not in ("time", "throughput"):
        raise ValueError("metric must be 'time' or 'throughput'")
    if not isinstance(data.get("unit"), str) or not data["unit"].strip():
        raise ValueError("unit must be a nonempty string")
    if "environment" in data and not isinstance(data["environment"], dict):
        raise ValueError("environment must be an object")
    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("cases must be a nonempty list")
    # Validate ALL measurements first; do not silently omit malformed cases.
    seen: set[str] = set()
    normalized: list[tuple[str, list[float]]] = []
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError("each case must be an object")
        name = case.get("name")
        if not isinstance(name, str) or not name.strip() or name in seen:
            raise ValueError("case names must be nonempty and unique")
        seen.add(name)
        pairs = case.get("pairs")
        if not isinstance(pairs, list) or not pairs:
            raise ValueError(f"{name}: pairs must be a nonempty list")
        logs: list[float] = []
        for i, pair in enumerate(pairs):
            if not isinstance(pair, dict):
                raise ValueError(f"{name}: pair {i} must be an object")
            baseline = positive_number(pair.get("baseline"), f"{name} pair {i} baseline")
            candidate = positive_number(pair.get("candidate"), f"{name} pair {i} candidate")
            # Taking log of a representable ratio avoids cancellation from
            # subtracting two large, nearly equal logs. Fall back for extreme ratios.
            numerator, denominator = (baseline, candidate) if metric == "time" else (candidate, baseline)
            ratio = numerator / denominator
            log_ratio = math.log(ratio) if 0 < ratio < math.inf else math.log(numerator) - math.log(denominator)
            logs.append(log_ratio)
        normalized.append((name, logs))
    alpha = (1.0 - confidence) / (len(cases) if bonferroni else 1)
    if not 0 < alpha < 1:
        raise ValueError("confidence adjustment is outside representable range")
    rng = random.Random(seed)
    results: list[dict[str, Any]] = []
    for name, logs in normalized:
        n = len(logs)
        estimate = finite_exp(math.fsum(logs) / n)
        if n < min_pairs:
            results.append({"name": name, "pairs": n, "speedup": estimate,
                            "interval": None, "status": "INCONCLUSIVE",
                            "reason": f"need at least {min_pairs} independent paired observations"})
            continue
        resamples = sorted(math.fsum(logs[rng.randrange(n)] for _ in range(n)) / n
                           for _ in range(bootstrap))
        lower = finite_exp(quantile(resamples, alpha / 2))
        upper = finite_exp(quantile(resamples, 1 - alpha / 2))
        # Be conservative at an exact/near-exact floating-point gate boundary.
        # This rounding guard is not statistical uncertainty or an error proof.
        guard = 16 * sys.float_info.epsilon * max(minimum_speedup, lower, upper)
        status = "PASS" if lower - minimum_speedup > guard else "REGRESSION" if minimum_speedup - upper > guard else "INCONCLUSIVE"
        results.append({"name": name, "pairs": n, "speedup": estimate,
                        "interval": [lower, upper], "numerical_gate_guard": guard,
                        "status": status})
    statuses = {case["status"] for case in results}
    overall = "REGRESSION" if "REGRESSION" in statuses else "INCONCLUSIVE" if "INCONCLUSIVE" in statuses else "PASS"
    return {"schema_version": 1, "analysis": "paired-log-ratio-percentile-bootstrap",
            "metric": metric, "unit": data["unit"], "environment": data.get("environment", {}),
            "minimum_speedup": minimum_speedup, "requested_confidence": confidence,
            "per_case_confidence": 1 - alpha, "bonferroni": bonferroni,
            "bootstrap_resamples": bootstrap, "seed": seed, "min_pairs": min_pairs,
            "overall": overall, "cases": results,
            "limitations": "Requires meaningful independent pairs; not a proof, p99 analyzer, or memory/quality gate."}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--minimum-speedup", type=float, default=0.95)
    parser.add_argument("--confidence", type=float, default=0.95)
    parser.add_argument("--bootstrap", type=int, default=10000)
    parser.add_argument("--min-pairs", type=int, default=10)
    parser.add_argument("--seed", type=int, default=20260905)
    parser.add_argument("--bonferroni", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = analyze(load_json(args.input), minimum_speedup=args.minimum_speedup,
                         confidence=args.confidence, bootstrap=args.bootstrap,
                         min_pairs=args.min_pairs, seed=args.seed, bonferroni=args.bonferroni)
        rendered = json.dumps(result, indent=2, allow_nan=False) + "\n"
        if args.output:
            args.output.write_text(rendered, encoding="utf-8")
        print(rendered, end="")
    except (OSError, ValueError, TypeError, OverflowError) as exc:
        print(f"Invalid benchmark input or options: {exc}", file=sys.stderr)
        return 2
    return {"PASS": 0, "REGRESSION": 1, "INCONCLUSIVE": 3}[result["overall"]]


if __name__ == "__main__":
    raise SystemExit(main())
