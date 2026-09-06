# Performance budget and design review

Complete before implementation or a significant architecture change. Use the
[prevention guide](../references/fast-by-default.md) and existing
[report template](performance-report.md). `TBD` means unvalidated, not unlimited.
No illustrative number in this package is a default production SLO.

## Objective and semantic contract

- Useful operation and affected users/callers:
- Start and usable-completion boundary:
- Exactness, output quality, freshness, ordering, durability, error behavior:
- Workload/corpus identity, size/skew, expected growth, cold/warm modes:
- Required device/CPU/runtime/deployment cohorts:
- Offered load, arrival model, concurrency, and degraded modes:
- Decision owner and review date:

## Budget ledger

| Metric and unit | Boundary/cohort/load/window | Absolute limit | Approved baseline / relative gate | Measurement and uncertainty policy | Owner |
|---|---|---|---|---|---|
| End-to-end latency distribution | TBD | TBD | TBD | Counts, histogram resolution, tail evidence | TBD |
| Valid successful goodput and error rate | TBD | TBD | TBD | Offered/admitted/completed/failed denominators | TBD |
| CPU seconds per valid operation | TBD | TBD | TBD | Process/fleet scope, paired-run policy | TBD |
| Peak / post-burst retained memory | TBD | TBD | TBD | Live bytes, capacity, RSS/cgroup attribution | TBD |
| In-flight / queue items and bytes | TBD | TBD | TBD | Overload and slow-consumer phases | TBD |
| Startup / first-use cost | TBD | TBD | TBD | Precisely defined cold state | TBD |
| Output quality / size / cost per useful unit | TBD | TBD | TBD | Unchanged semantics/accounting scope | TBD |

Select only applicable metrics; justify exclusions. For a service, correctness,
latency, failure behavior, and overload limits normally need explicit treatment.
Keep the configurable normalized-speedup gate distinct from absolute requirements.
The paired benchmark tool does not implement all gates in this table.

## Critical-path and work map

| Stage / dependency / owner | Blocking or overlapping work | Calls and bytes per operation | State lifetime and limits | Evidence or assumption | Candidate simplification |
|---|---|---|---|---|---|
| TBD | TBD | TBD | TBD | TBD | TBD |

Explain overlap and shared work; do not add inclusive spans or per-stage p99s as
if they were independent elapsed-time components. Include misses, initialization,
retries, merging, consumer delivery, and cleanup where users pay those costs.

## Verification and operation

- Correctness oracle and adversarial cases:
- Local/PR checks, commands, data, target coverage:
- Controlled load/soak/recovery checks and safety bounds:
- Production observation, cohort breakdown, overhead/privacy limits:
- Result for unavailable tools, missing evidence, or inconclusive measurements:
- Rollback/mitigation trigger and authorized action:
- Exception reason, owner, expiry, and replacement check (when applicable):
- Baseline/corpus version policy and recurring cleanup review:

Decision: proceed / revise / blocked by evidence. Label every key claim as
measured, derived, hypothesized, or unvalidated.
