# Measurement and diagnosis

Read this before modifying a hot path. Source IDs resolve in
[sources.md](sources.md). The workflow and gates below are this skill's suggested
engineering policy, not numerical recommendations attributed to Algorithmica.

## Define what one observation means

A benchmark case is a workload, target, build, and measurement boundary. A useful
name encodes size, distribution, and mode, such as
`histogram/64KiB/skewed/reused-buffer/one-worker`. Freeze the corpus and record
its hash. Keep compiler flags, allocator settings, and worker count in the
result, not in someone's memory. [A01, A02]

Measure both the isolated mechanism and the entire operation. A pool's lookup
benchmark excludes a miss, initialization, locking, and post-burst retention;
a kernel benchmark can exclude a costly AoS-to-SoA conversion. Neither alone
answers whether the application improved.

For a service, distinguish offered load, achieved throughput, service time,
queueing time, and response latency. Do not infer p99 response latency from the
median of batch-average runtimes. Preserve realistic arrival rates and avoid a
load generator that stops issuing work during a stall and thereby conceals it.
Treat this as a workload-design requirement; the included script analyzes paired
scalar metrics, not a complete service-load experiment.

## Build a workload matrix

Include sizes around actual algorithm and hardware boundaries: zero, one,
`W-1`, `W`, `W+1`, multiples plus tails, page boundaries, cache transitions, and
large streaming inputs. Add random, sorted, reverse-sorted, duplicate-heavy,
sparse, all-equal, highly skewed, and representative production inputs where
meaningful. Run both typical and adversarial cases. [A02, A17]

Separate first-call/startup, cold working set, and warm steady state. A warmed
256-element array and a stream larger than the last-level cache are different
experiments. Do not clear global OS caches or change host-wide power settings
without authorization. Label controlled-machine measurements separately from
shared-runner observations.

For allocation changes, add repeated small requests, repeated large requests,
alternating sizes, cross-thread release, and a large burst followed by a long
small-request phase. Measure retained capacity throughout, not only at exit.

## Benchmark hygiene

Use release-like builds. Construct randomized inputs outside a kernel-only timed
region, consume the outputs, and test correctness separately. `black_box` is a
best-effort optimization barrier, not a guarantee that any benchmark is valid.
Avoid adding a volatile access or memory fence to every operation unless it is
part of the real workload. Inspect suspiciously tiny timings. [R05]

Interleave independent baseline/candidate batches in randomized AB/BA order.
A batch must be long enough that timer overhead is immaterial, but short enough
to expose drift. Preserve raw observations and run identifiers. Pair comparable
trials; array position is not a scientific justification for pairing unrelated
measurements. Keep a held-out corpus when tuning thresholds.

Record CPU model and active core class, OS, compiler, flags, enabled ISA,
allocator, thread count, affinity, input, power/thermal conditions, and background
load. Wall time is the user-facing metric; cycles help explain CPU behavior but
do not automatically remove effects of frequency, memory, migration, or stalls.
[A02, T02]

## Locate the bottleneck

| Evidence to collect | Hypothesis to investigate | First experiment |
|---|---|---|
| Large allocation or initialization share | Per-item ownership or repeated clearing | Reuse bounded scratch; time zeroing separately |
| High streaming traffic | Bandwidth or extra passes | Fuse passes; reduce bytes per item |
| Dependent load stalls, low achieved bandwidth | Pointer-chasing latency | Compact layout; batch independent lookups |
| Frequent costly mispredictions | Data-dependent control flow | Partition work; compare branchy and masked variants |
| Long dependency chain | Latency rather than operation throughput | Independent accumulators; reassociate only when legal |
| Poor scaling and shared writes | Contention, false sharing, or bandwidth saturation | Worker-local state; partition output |
| Vector source, scalar machine loop | Unsupported operations or legality/cost model | Inspect vectorization remarks and scalar calls |

Do not diagnose bandwidth saturation from cache misses alone. Distinguish cache
miss frequency, total bytes, memory-level parallelism, and loaded latency.
[A04, A23]

On Linux, start with a small counter set and sampling:

```sh
perf stat -r 10 -e cycles,instructions,branches,branch-misses,page-faults -- ./app
perf record -g -- ./app
perf report
```

Commands require a suitable local installation and permissions. `perf list`
reveals supported events. Generic cache counters are not equivalent across CPUs.
Too many events can multiplex counters; inspect time-running/scaling and use
focused repeated experiments. Do not compare multiplexed ratios blindly. [T02]

Use a platform-native sampling and allocation profiler on other OSes. Preserve
symbols and sufficient unwind information. Sampling, instrumentation, and
allocator tracing have different perturbation costs; profile for diagnosis and
measure final performance without heavyweight instrumentation. [A24]

## Model before tuning

Amdahl model: `S = 1 / ((1-p) + p/s)`. If a component accounts for 10% of runtime,
even eliminating it caps idealized overall speedup at `1/0.9`. This is arithmetic
under the stated fixed-work assumption, not a prediction of cache interactions.

For a streaming kernel, model `T >= bytes_transferred / sustainable_bandwidth`.
For compute, estimate useful operations and attainable execution throughput.
Use a roofline-style `attainable_rate <= min(compute_ceiling, bandwidth *
operational_intensity)`, with an explicitly named memory level. Account for
write allocation, rereads, scratch buffers, and output traffic. Treat this as a
bound/model to test, not an exact time formula. [A23, A25]

A model can reject an implausible claim. It cannot certify a microarchitecture's
latency from a generic instruction table.

## Acceptance and statistics

The supplied script estimates the geometric mean of **paired speedup ratios**
and a percentile-bootstrap interval by resampling complete pairs. It reports
PASS when the interval's lower bound clears the configured floor, REGRESSION
when the upper bound is below it, and INCONCLUSIVE otherwise. This is an explicit
operational choice. It is not a distribution-free guarantee. Endpoints at or
within a small floating-point guard of the threshold are conservatively
INCONCLUSIVE; the guard is not a substitute for statistical uncertainty.

Independence, meaningful pairing, and representative inputs remain the caller's
responsibility. Autocorrelated samples require batch/block-aware analysis. Many
simultaneous comparisons may require a family-wise policy; the script offers
optional Bonferroni adjustment. A tiny sample cannot be rescued by many bootstrap
resamples. Do not rerun until an initially failing experiment happens to pass.

Keep separate limits for retained bytes, peak RSS, allocation counts, output
size/quality, and tail latency. Report every required case. A weighted aggregate
may summarize known production weights, but must not replace those cases.
