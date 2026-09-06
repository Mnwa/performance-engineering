# Load, capacity, and recovery experiment

Use with [latency-load-capacity.md](../references/latency-load-capacity.md).
This is an experiment specification, not authorization to load a production
system. Fill every applicable field before running; attach actual results later.

## Contract and environment

Operation / correctness oracle / usable-completion boundary:
Required latency, goodput, errors, quality, CPU, and memory limits:
Baseline and candidate revisions; dependency/compiler/allocator versions:
CPU architecture, affinity policy, effective cgroup limits, replica count:
Generator location/capacity, target location, topology and allowed scope:
Corpus hash, size/skew, cache state, output consumer, data-aging assumptions:
Permissions, maximum generated work/bytes, abort conditions, cleanup owner:

## Arrival and measurement policy

Choose open or closed model and explain why it represents the requirement.
Record planned arrivals, actual dispatch/admission, starts, finishes, usable
completion, failures, deadlines, cancellations, and remaining work where relevant.
Define time units, clock source/cross-host limitations, correlation, and overlap.
Record generator lag and dropped iterations rather than assuming configured load
was achieved. Define valid goodput and the outcome denominator explicitly.

## Phases

| Phase | Offered load and distribution | Duration rationale | Resource/queue safety cap | Required observation | Acceptance |
|---|---|---|---|---|---|
| Startup / warm-up | TBD | TBD | TBD | First-use and initialization | TBD |
| Representative steady state | TBD | TBD | TBD | Baseline distribution and resources | TBD |
| Expected peak / capacity sweep | TBD | TBD | TBD | Goodput, tails, saturation mechanism | TBD |
| Burst / overload | TBD | TBD | TBD | Admission, queue bytes, timeout/retry behavior | TBD |
| Soak / data aging | TBD | TBD | TBD | Retention, eviction, rotation, cleanup | TBD |
| Degraded dependency (authorized only) | TBD | TBD | TBD | Amplification, isolation, cancellation | TBD |
| Recovery at original load | TBD | TBD | TBD | Drain time, restored SLO, retained memory | TBD |

Explain any omitted phase. Predefine repetitions and comparison order; preserve
raw samples and environment drift. Do not rerun indefinitely until a pass.

## Instrumentation and result schema

Per cohort and phase: observation count, offered/admitted/valid-completed rates,
rejections/timeouts/errors, latency histogram/quantiles, generator lag, in-flight
and queue items/bytes, CPU, memory/retention, and relevant resource-pressure data.
Include the diagnostics proving the intended work ran and note their overhead.
Use uninstrumented or appropriately low-overhead runs for final timing.

Define histogram compatibility/resolution and timeout treatment. Do not average
instance p99s, substitute batch means for request samples, or feed unrelated
observations into a paired bootstrap. The bundled comparator is not a load
generator, tail-latency analyzer, or complete budget checker.

## Decision and recovery evidence

Per-budget status: PASS / FAIL / INCONCLUSIVE / NOT RUN, with evidence links.
Maximum useful load meeting the contract and its uncertainty:
Recovery/drain time and post-burst memory:
Remaining bottleneck and next discriminating experiment:
Keep/revert/mitigate decision and authorized owner:
