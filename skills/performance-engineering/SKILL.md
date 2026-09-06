---
name: performance-engineering
license: MIT
description: Design, implement, profile, and optimize CPU software using measured bottlenecks, hardware-aware algorithms, bounded allocation, cache-efficient layouts, numerical contracts, and SIMD. Use for slow code, hot loops, allocation churn, memory growth, compute kernels, vectorization, performance reviews, or regression investigation. Includes Rust and C++ guidance.
compatibility: >-
  Language-agnostic workflow. The bundled examples need a C++17 compiler; the Rust
  examples need Cargo. The scripts need Python 3.9+ and no third-party packages.
  AArch64/NEON paths require native AArch64 execution to be exercised. Every
  performance conclusion requires measurement on the consuming project's own
  workload and target CPUs.
metadata:
  version: "1.0.0"
  last-verified: "2026-09-05"
---

# Performance engineering

Make the required work cheaper, then make the remaining work run efficiently.
An optimization is a hypothesis until it passes correctness and representative
measurement. Do not confuse a lower instruction count, fewer allocations, or
wider vectors with a faster application.

## Scope and source policy

Use this skill for CPU-side software: libraries, services, parsers, compression,
search, numerical kernels, and data-processing pipelines. It is not a complete
GPU, distributed-systems, or cryptographic implementation manual.

The conceptual foundation is Algorithmica's *Algorithms for Modern Hardware*.
The references extend it with allocation engineering, numerical safeguards,
SIMD portability, and an executable validation workflow. See
[the source index](references/sources.md). Published case-study speedups are
historical measurements, not promises for another compiler or processor.

Follow the repository's language, safety, API, and compatibility rules. Do not
rewrite the project in Rust or C++ merely because examples use them. Verify
version-sensitive library APIs and ISA requirements before implementing them.

## Start here

Inspect the code, tests, build configuration, dependency lockfile, benchmarks,
existing profiles, and target platforms. Establish the following contract from
available information; explicitly label anything still assumed:

- **Work:** input sizes, distributions, frequency, throughput versus latency,
  concurrency, startup versus steady state, and output quality.
- **Correctness:** exactness, overflow, ordering and ties, floating-point error,
  invalid inputs, determinism, and security-sensitive behavior.
- **Resources:** CPU targets, memory budget, retained memory, allocation budget,
  supported compilers, and allowed implementation complexity.

For new software, first create a simple correct baseline and representative
workloads. For existing software, reproduce the complaint before changing it.
For a review without execution access, provide ranked hypotheses and a runnable
measurement plan; never invent a profile or a measured speedup.

## Read only the relevant references

| Current question | Reference |
|---|---|
| What is slow, and how do we know? | [Measurement](references/measurement.md) |
| Allocations, pools, zeroing, retained memory | [Allocations](references/allocations.md) |
| Cache misses, pointer chasing, data layout | [Memory and layout](references/memory-and-layout.md) |
| Arithmetic, dependencies, division, approximations | [Computations](references/computations.md) |
| Vectorization, intrinsics, masks, SIMD recipes | [SIMD](references/simd.md) |
| Choosing or replacing an algorithm | [Algorithm patterns](references/algorithms.md) |
| Rust implementation or SIMD-library choice | [Rust](references/rust.md) |
| Worker count, ownership, contention, NUMA | [Parallelism](references/parallelism.md) |

## Required workflow

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

Normalize as `baseline_time / candidate_time` for time and
`candidate_rate / baseline_rate` for throughput. Note that a `0.95` time-speedup
floor allows a time increase of about `5.263%`; use `1/1.05` for a strict `5%`
time-increase allowance. The included paired-bootstrap utility implements the
first definition, not a universal statistical policy.

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

## Included implementation material

[Examples](examples/README.md) contain original correctness-oriented Rust and
C++ kernels. They are teaching and experiment starting points, not claims of
being faster than a standard library. [Verification](scripts/verify.py) runs the
checks available in the current environment and records skips. Read
[the validation record](validation/README.md) before relying on target coverage.
