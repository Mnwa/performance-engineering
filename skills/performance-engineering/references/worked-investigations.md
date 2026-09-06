# Worked performance investigations

These are **original hypothetical scenarios**, not production incidents,
measurements from either book, or promises of speedup. They demonstrate how an
agent should choose and reject experiments. Source IDs resolve in
[sources.md](sources.md); the numerical consequences are derived under each
scenario's stated assumptions.

## 1. Low host CPU, high service latency

**Given:** a container has 16 visible logical CPUs, `cpu.max = 200000 100000`,
16 workers, periodic latency spikes, and low host-wide CPU utilization.

**Do not conclude:** the service has abundant CPU, or the fix is 32 workers.
Visible CPUs and a two-CPU aggregate quota are different constraints. [O01]

**Investigate:** correlate arrivals, executor queue delay, runnable delay, and
cgroup usage/throttling deltas during the spikes. Check ancestor limits and the
effective cpuset. Establish whether the dependency is also slow; a throttle
counter by itself does not identify every request's delay.

**Experiment:** compare a bounded concurrency sweep at the same offered load
and quota; alternatively compare an authorized quota change while holding other
variables fixed. Measure goodput, p99, rejections, CPU per valid operation,
queue bytes, and retained scratch. Keep the smallest configuration meeting the
contract, not the one with the most workers.

**Disconfirming evidence:** spikes occur without relevant scheduling pressure,
and dependency spans explain the critical path. Redirect the investigation
rather than forcing a CPU explanation.

## 2. A hot function is not most of the request

**Given:** a sequential 100 ms operation contains 10 ms CPU and 90 ms wait. A
function is 60% of CPU samples. Assume samples represent CPU time accurately.

**Derivation:** its contribution is 6 ms. A 2x local improvement gives a 97 ms
operation and `100/97 ≈ 1.031x` speedup. The same percentage cannot be treated as
60% of wall time. With concurrency, queueing, or changing overlap, even that
simple model needs revalidation.

**Investigate:** measure absolute CPU demand and build a non-overlapping critical
path using [thread-state reasoning](systems-performance.md). Ask whether the
function is also a fleet CPU-cost issue even when it is not the latency limit.

**Decision:** optimize it only for the named objective; separately investigate
whether the 90 ms wait is unnecessary work, queuing, or a required dependency.
A CPU-saving change may be worthwhile without being a latency breakthrough.

## 3. Compression kernel improves, pipeline gets worse

**Given:** an isolated compressor benchmark improves, but an end-to-end batch
shows higher p99 and post-burst RSS after increasing workers and adding reusable
scratch. No conclusion about the real cause is yet justified.

**Investigate:** include setup, dictionary/state initialization, scheduling,
compression, output merge, and consumer progress. Record per-worker retained
capacity, total in-flight input/output, allocations, CPU, and memory pressure.
Run mixed file sizes, skewed compressibility, and a large burst followed by small
files. Compare one worker before considering scaling.

**Experiment:** separate the kernel change, concurrency change, and pooling
policy into independent candidates. Bound global retained bytes and in-flight
output. Compare compression validity and size/quality as well as time. The
existing [allocation](allocations.md), [SIMD](simd.md), and
[parallelism](parallelism.md) references supply the low-level investigations.

**Decision:** a microbenchmark win cannot override a required pipeline latency,
memory, or quality gate. The correct response may be to keep the kernel and
revert the concurrency/pooling changes rather than reject all optimization.

## 4. A cache looks excellent until synchronized misses

**Given:** warm-cache tests are fast, but many requests for an expired popular
key trigger overlapping recomputation, pool waits, and timeouts.

**Investigate:** separate hit, miss, fill, eviction, and failure paths. Count
concurrent fills per key, retained bytes, dependency attempts, and discarded
work. Check whether the bottleneck is computation or a downstream limit.

**Experiment:** compare an application-appropriate bounded fill/coalescing policy
with the baseline. Preserve freshness, failure isolation, and cancellation.
Exercise fill failure and a waiting caller's deadline; never hold a global lock
across unrelated slow fills merely to reduce duplicate work.

**Decision:** evaluate useful output and miss behavior, not hit rate alone. Any
stale-result policy is a correctness/API decision requiring explicit permission,
not a performance-only implementation detail. [O08]

## 5. Benchmark stops sending work during a stall

**Given:** ten clients each send a request only after the previous one completes.
A target stalls, the generator sends fewer requests, and the reported latency
looks better than users see under independent arrivals.

**Investigate:** identify the intended traffic model; closed clients are valid
for some user behavior but not equivalent to a fixed external arrival process.
Compare planned/actual arrivals, dispatch lag, generator capacity, timeout counts,
and in-flight work. [O07, S06]

**Experiment:** where independent arrivals represent the requirement, run an
arrival-rate test with explicit safety/concurrency bounds and missed-arrival
accounting. Do not repair the result by silently inserting invented observations
or discarding failed requests. Analyze overload and recovery separately from a
steady-state comparison.

## 6. Every change passes, but the release is much slower

**Given:** each of ten changes increases latency by 2%; a relative check against
the immediately previous change allows them all.

**Derivation:** the cumulative multiplier is `1.02^10 ≈ 1.219`, or about a 21.9%
increase. Passing an individual tolerance does not preserve an absolute target.

**Experiment and policy:** retain an approved release baseline, enforce the
absolute latency/resource budget, and review long-term trends per workload.
Do not automatically reset a failing budget or lower the test's offered load.
See [fast-by-default.md](fast-by-default.md). This is an original example and
policy recommendation, not a numeric rule from the books.
