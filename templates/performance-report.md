# Performance change report

## Decision

**Keep / revert / inconclusive / proposal only:**

One paragraph stating the user-visible result and remaining uncertainty. Label
numbers as **measured**, **derived**, **hypothesized**, or **unvalidated**.

## Contract

- Workloads, sizes, distributions, target CPUs, and execution mode:
- Required correctness, ordering, numeric error, quality, and compatibility:
- Primary objective and separate latency/memory/quality limits:
- Configured no-regression floor and uncertainty policy:

## Reproduction

Baseline commit/build:
Candidate commit/build:
Corpus identity/hash and generation seed:
CPU/OS/compiler/flags/ISA/allocator/workers:
Exact correctness, profiling, and benchmark commands:
Raw samples and profiler outputs:
Measurement boundary; included/excluded setup and cleanup:
Run ordering, pairing, warmup, and known machine noise:

## Diagnosis and hypothesis

Measured hot-path share and evidence:
Limiting mechanism, not only function name:
Transformation and why it should affect that mechanism:
Amdahl/traffic/allocation/error bound, with assumptions:
Failure mode and expected unfavorable workload:

## Implementation

Algorithm/data-layout/ownership change:
Added and removed passes, bytes, allocations, initialization:
Dispatch, scalar fallback, tail handling, ISA requirements:
Unsafe invariants or floating-point contract changes:
Maintenance and portability cost:

## Correctness evidence

Reference/oracle and differential tests:
Empty/tiny/boundary/misaligned/adversarial/maximum-value tests:
Ordering, collisions, overflow, numeric-domain tests:
Native targets actually exercised:
Sanitizer/concurrency/interpreter checks:
Tests unavailable, skipped, or not performed:

## Per-case results

| Required case / target | Baseline | Candidate | Normalized speedup | Interval | Gate |
|---|---:|---:|---:|---|---|
| Replace with raw-sample-backed measurements | — | — | — | — | — |

Use baseline/candidate for elapsed time and candidate/baseline for throughput.
Do not substitute a geometric mean for required individual cases. Separate
startup, cold, warm, streaming, and end-to-end results where relevant.

Memory: allocation calls, allocated bytes, peak live bytes, peak RSS, retained
capacity and post-burst RSS. Distinguish what was actually observable.
Quality: output validity, size/quality, error and threshold-decision differences.
Service: offered load, achieved rate, queue bounds and response-latency tails.

## Interpretation and next decision

Did the intended mechanism change in the post-change profile?
Did the full application improve beyond measurement uncertainty?
Which cases regressed, and are they required cases?
What is the tradeoff in memory, numerical behavior, complexity, or portability?
What supports keeping/reverting the change? What remains unvalidated?
