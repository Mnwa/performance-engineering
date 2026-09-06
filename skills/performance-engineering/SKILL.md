---
name: performance-engineering
license: MIT
description: Design, diagnose, and optimize software using user-facing performance budgets, systems analysis, representative measurement, hardware-aware algorithms, bounded allocation, numerical contracts, and SIMD. Use for slow code, latency, throughput, CPU or memory pressure, queues, capacity, performance reviews, new-system design, and regression prevention. Includes Rust and C++ guidance.
compatibility: >-
  Language-agnostic workflow. The bundled examples need a C++17 compiler; the Rust
  examples need Cargo. The scripts need Python 3.9+ and no third-party packages.
  AArch64/NEON paths require native AArch64 execution to be exercised. Every
  performance conclusion requires measurement on the consuming project's own
  workload and target CPUs.
metadata:
  version: "1.1.0"
  last-verified: "2026-09-06"
---

# Performance engineering

Make the required work cheaper, then make the remaining work run efficiently.
An optimization is a hypothesis until it passes correctness and representative
measurement. Do not confuse a lower instruction count, fewer allocations, or
wider vectors with a faster application.

## Scope and source policy

Use this skill for libraries, services, parsers, compression, search, numerical
kernels, and data-processing pipelines, including the operating-system and
request-path constraints that determine their performance. It is not a complete
GPU, distributed-systems, database, or cryptographic implementation manual.

The low-level foundation is Algorithmica's *Algorithms for Modern Hardware*.
Systems diagnosis draws on Brendan Gregg's *Systems Performance: Enterprise and
the Cloud*, second edition, and his public methodology guides. Prevention and
lifecycle guidance draw on Den Odell's public *Fast by Default* model and the
publisher's early-access book material. Full book texts were not accessed for
this update. See [the source index](references/sources.md) for access boundaries,
check dates, and supporting primary documentation. Do not invent unavailable
chapter content or formal framework details. Historical case-study speedups are
not promises for another compiler, processor, or deployment.

Follow the repository's language, safety, API, and compatibility rules. Do not
rewrite the project in Rust or C++ merely because examples use them. Verify
version-sensitive library APIs and ISA requirements before implementing them.

## Start here

Inspect the code, tests, build configuration, dependency lockfile, benchmarks,
existing profiles, and target platforms. Establish the following contract from
available information; explicitly label anything still assumed:

- **Work:** input sizes, distributions, frequency, throughput versus latency,
  concurrency, arrival model, startup versus steady state, and output quality.
  Name the user/caller operation and its usable-completion boundary.
- **Correctness:** exactness, overflow, ordering and ties, floating-point error,
  invalid inputs, determinism, and security-sensitive behavior.
- **Resources:** CPU targets, memory budget, retained memory, allocation budget,
  supported compilers, effective CPU/container limits, queue/in-flight bounds,
  and allowed implementation complexity.
- **Budgets and ownership:** absolute latency/goodput/resource targets, required
  cohorts and load, relative regression policy, evidence needed for a decision,
  and the owner of the benchmark and rollout/rollback decision.

For new software, create a [performance budget](templates/performance-budget.md),
a simple correct baseline, and representative workloads. For existing software,
reproduce the complaint before changing it.
For a review without execution access, provide ranked hypotheses and a runnable
measurement plan; never invent a profile or a measured speedup.

## Read only the relevant references

| Current question | Reference |
|---|---|
| What is slow, and how do we know? | [Measurement](references/measurement.md) |
| Whole-system problem, critical path, USE/TSA, on/off-CPU | [Systems performance](references/systems-performance.md) |
| CPU limits, pressure, filesystem/storage/network, cloud | [OS diagnostics](references/operating-system-diagnostics.md) |
| Tail latency, arrival models, queueing, overload/recovery | [Latency and capacity](references/latency-load-capacity.md) |
| Design budgets, development feedback, CI, ownership | [Fast by Default](references/fast-by-default.md) |
| Concrete diagnostic examples and rejected conclusions | [Worked investigations](references/worked-investigations.md) |
| Allocations, pools, zeroing, retained memory | [Allocations](references/allocations.md) |
| Cache misses, pointer chasing, data layout | [Memory and layout](references/memory-and-layout.md) |
| Arithmetic, dependencies, division, approximations | [Computations](references/computations.md) |
| Vectorization, intrinsics, masks, SIMD recipes | [SIMD](references/simd.md) |
| Choosing or replacing an algorithm | [Algorithm patterns](references/algorithms.md) |
| Rust implementation or SIMD-library choice | [Rust](references/rust.md) |
| Worker count, ownership, contention, NUMA | [Parallelism](references/parallelism.md) |

## Required workflow

### 0. Select the scope and prevention/investigation path

For an application complaint, move from useful-operation latency to the critical
path, thread states, limiting resources, and finally code. Use workload
characterization and USE/TSA when the limiting stage is unknown. Do not jump to
SIMD because the repository contains a hot loop. A kernel-only task may begin
with its measured CPU/memory mechanism, but must retain an end-to-end check.

For a new feature, map calls, bytes, handoffs, state lifetime, and concurrency
before implementation. Define budgets, a baseline/oracle, and verification
ownership. Read only the reference needed for the current stage; do not load the
entire bundle or require every diagnostic for a small local change.

### 1. Establish a trustworthy baseline

Build with production-like optimization and target features. Separate setup,
allocation, initialization, kernel execution, and cleanup measurements where
useful, but retain an end-to-end benchmark containing the costs users pay.
Record environment, commands, input identity, and raw samples. Preserve a scalar
or otherwise simple correctness oracle.

### 2. Identify a limiting mechanism

Use a CPU profile, allocation profile, wall-clock breakdown, and suitable hardware
counters. Classify the main limitation: unnecessary work, bandwidth, dependent
memory latency, branch recovery, arithmetic throughput, arithmetic dependency
latency, allocation/initialization, synchronization, I/O, or front-end/code size.
A hot function is a location, not a diagnosis. Counter values are clues, not proof.
For a service, also test admission/executor queueing, runnable delay, quota
throttling, downstream waits, and overload. CPU-profile percentages are not
percentages of request wall time. Separate useful work, intentional idle, and
critical-path waiting; never add overlapping spans or all threads' waits.

Keep an evidence ledger: observation with scope/denominator, competing hypothesis,
expected effect, discriminating experiment, and disconfirming result. Unknown
metrics remain unknown. Actively observe the benchmark and generator to verify
that the intended valid work, not a shortcut or failure path, is being measured.

Estimate potential benefit. For a fraction `p` of baseline execution accelerated
by `s`, the idealized overall speedup is `1 / ((1-p) + p/s)`. State assumptions;
interactions with caching, parallelism, and input distribution can change them.

### 3. Choose the least costly effective transformation

Normally try this order, changing it only when evidence warrants:

1. Remove repeated work, unnecessary passes, copying, and unsuitable algorithms.
2. Improve representation, locality, object size, and ownership boundaries.
3. Bound allocations and reuse; reduce justified initialization work.
4. Expose invariants, simplify hot loops, and enable compiler optimization.
5. Improve dependency structure, batching, and instruction-level parallelism.
6. Add explicit SIMD where it improves the identified mechanism.
7. Add or tune parallelism without exceeding memory and bandwidth budgets.

Write down the expected effect and failure mode before implementing. Keep
independent experiments separable. Do not pile on speculative changes.

### 4. Preserve the semantic contract

For integers, distinguish wrapping, checked, saturating, and mathematical
arithmetic. For floating point, specify precision, rounding/reassociation,
NaN/infinity/subnormal behavior, and application-level error. For searches and
argmin, preserve first/last match and tie policy. For compression, test output
validity and size/quality, not just encoding time.

Use a scalar tail or a demonstrably safe masked operation. Never read beyond an
allocation and then discard the result. Never read uninitialized memory. An
aligned address, a valid index, and a supported instruction set are separate
proof obligations. Unsafe code requires local safety comments and adversarial
tests; it is not a default performance technique.

### 5. Inspect the result, not the source's appearance

Inspect optimized assembly or optimization remarks for the actual hot path:
vectorization, scalarized gathers, bounds checks, divisions, calls, spills,
reductions, redundant initialization, and feature-dispatch placement. A vector
API can lower to scalar instructions. A clean scalar loop can already vectorize.

### 6. Validate and decide

Differentially test empty/tiny inputs, vector boundaries, misaligned starts,
duplicates, sparse and skewed data, maximal values, and error cases. Exercise
fallbacks directly. Run sanitizers or language-appropriate memory/concurrency
checks separately from performance measurements.

Benchmark representative size and distribution buckets with paired,
interleaved baseline/candidate trials. Re-profile the full application. Measure
peak and post-burst retained memory as well as runtime. Keep an optimization only
when its application benefit justifies its maintenance and portability costs.

For queued/shared systems, validate the arrival model and use a
[load-test plan](templates/load-test-plan.md) covering applicable peak, burst,
soak, degraded-dependency, and recovery behavior. Keep errors, dropped arrivals,
retries, and generator lag visible. Do not average per-instance quantiles or
infer request p99 from batch means. Use dedicated tail/resource analyses; the
bundled paired-scalar comparator does not certify those budgets.

### 7. Prevent the next regression

Keep the accepted case, workload identity, absolute budget, and reviewed release
baseline. Put reliable cheap checks near development and heavier load/target
checks on an appropriate controlled stage. Mark pending, missing, and inconclusive
evidence explicitly. Define observation and rollback criteria, assign an owner,
and revisit obsolete dependencies, data growth, cache policy, and specializations.
Do not automatically rebaseline away a regression.

## Acceptance rules

Correctness is mandatory. Respect user-defined budgets and gates. Otherwise,
propose the following configurable starting gate rather than silently changing
the project's policy:

- Each required workload/target case must demonstrate normalized speedup
  `>= 0.95`, with an uncertainty-aware result; inconclusive is not a pass.
- A claimed improvement must also show a meaningful gain in its target objective.
  Merely passing the no-regression gate is not evidence of improvement.
- Memory, output quality, tail latency, and compatibility have separate gates.
  A geometric mean must not conceal a required case's regression.
- Absolute user-facing and resource budgets must also pass at the specified load.
  Repeated small regressions can violate them despite passing individual relative
  gates. Useful goodput must exclude invalid output and account for failures.

Normalize as `baseline_time / candidate_time` for time and
`candidate_rate / baseline_rate` for throughput. Note that a `0.95` time-speedup
floor allows a time increase of about `5.263%`; use `1/1.05` for a strict `5%`
time-increase allowance. The included paired-bootstrap utility implements the
first definition, not a universal statistical policy.

## Safe observation and experiments

Scope diagnostics to authorized processes and environments. Bound profiling and
load overhead, protect captured data, and state visibility gaps. Do not change
host-wide tunables, flush global caches, relax security, weaken durability, or
increase production traffic merely to obtain a cleaner benchmark. Controlled
fault/overload experiments require explicit authorization and safety limits.

## Avoid these unsupported claims

Do not say “stack is always faster,” “branchless is always faster,” “SIMD makes
this W times faster,” “the kernel zeros memory for free,” “a table lookup is
cheaper than arithmetic,” or “this allocator is best.” Name the conditions and
measure them. Never disable security checks, bounds checks, randomization, or
floating-point guarantees simply to improve a benchmark.

## Required output for an optimization task

Use [the report template](templates/performance-report.md). Report the contract,
baseline, diagnosis, changes, proof/testing, environment, per-case measurements,
resource tradeoffs, remaining uncertainty, and keep/revert decision. Mark each
result as measured, derived, hypothesized, or unvalidated. With no execution,
return a patch/proposal and explicit unvalidated items instead of fake numbers.
For design tasks, attach the budget and verification owner; for service changes,
attach the load/recovery evidence and per-budget outcome. Keep workload changes
and performance changes distinguishable.

## Included implementation material

[Examples](examples/README.md) contain original correctness-oriented Rust and
C++ kernels. They are teaching and experiment starting points, not claims of
being faster than a standard library. [Verification](scripts/verify.py) runs the
checks available in the current environment and records skips. Read
[the validation record](validation/README.md) before relying on target coverage.

[Behavioral evaluation scenarios](validation/performance-scenarios.md) test whether
an agent applies the expanded guidance. They are evaluation specifications, not
claims of executed model tests; the package verifier does not run them.

The [2026-09-06 extension validation](validation/books-update-2026-09-06.md)
records executed checks and limits for the systems/prevention addition.
