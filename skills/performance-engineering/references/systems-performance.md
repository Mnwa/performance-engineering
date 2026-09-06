# Systems performance: diagnose the mechanism before changing code

Use this guide when a complaint is about an application, service, host, or
container rather than an already-isolated kernel. Source IDs resolve in
[sources.md](sources.md). This is an original investigation workflow informed by
Brendan Gregg's public methodology material, not a reproduction of his book.
For host-specific collection, continue with
[operating-system diagnostics](operating-system-diagnostics.md).

## Start with a falsifiable problem statement

Record the operation that is slow, who or what is affected, when it started,
its measurement boundary, expected behavior, observed distribution, and recent
changes. Distinguish a regression from an unmet requirement or a capacity limit.
Characterize request sizes, arrival rates, concurrency, read/write mix, data
skew, working-set size, and batch versus interactive use. Method selection
precedes tool selection; avoid collecting whichever counters happen to be easy.
[S02]

An agent's first artifact should be a compact evidence ledger:

| Observation | Scope and denominator | Hypothesis | Discriminating experiment | Disconfirming result |
|---|---|---|---|---|
| p99 rises only during bursts | Complete requests at fixed offered load | Admission queue dominates | Trace enqueue/start/finish and queue depth | Queue stays short while downstream spans lengthen |
| A function is 60% of sampled CPU | One process, on-CPU samples | Excess computation | Measure its absolute CPU demand per valid operation | CPU demand is small relative to the critical path |
| RSS stays high after a large job | Whole process after quiescence | Retained scratch or fragmentation | Compare live objects, capacities, mappings, and later reuse | Live workload still requires the memory |

These are hypothetical examples, not measured findings. Keep alternatives alive
until an experiment separates them. Give each experiment a fixed workload,
expected direction of change, safety limit, and stop condition. Preserve the
failed hypotheses: they prevent repeated speculative tuning.

## Account for elapsed time, not just CPU samples

Gregg's thread-state analysis distinguishes execution, runnable delay, and
several kinds of waiting. Off-CPU analysis complements CPU profiling by showing
where threads stop executing; it also includes intentional inactivity. [S04, S05]

Build an application-specific critical-path timeline. Include admission queues,
executor queues, scheduled work, dependency calls, lock acquisition, I/O, and
response delivery as applicable. Propagate correlation identifiers across async
handoffs. An inclusive parent span already contains its children: do not add
both. Independent spans can overlap; sum only non-overlapping intervals on the
chosen critical path. Cross-host timestamps require clock-error awareness.

Do not equate all on-CPU time with useful computation: spinning and stalled
loads also execute on a CPU. Conversely, a sleeping worker may simply have no
work. Thread CPU totals and aggregate blocked-thread time may exceed request
wall time because several threads operate concurrently. A profile's percentage
needs its event, process/thread scope, and sample denominator attached.

For an original simplified example, a sequential operation spends 10 ms on CPU
and 90 ms waiting. A function occupying 60% of that CPU takes 6 ms, not 60 ms of
the operation. Making it twice as fast saves 3 ms, producing `100 / 97 ≈ 1.031`
idealized speedup, provided the wait and workload remain unchanged. This is a
derivation under stated assumptions, not a performance prediction.

## Use a resource inventory to avoid blind spots

The USE method asks about **utilization**, **saturation**, and **errors** for each
resource. Utilization can mean busy time or used capacity; saturation concerns
work beyond immediately available capacity. Check short intervals and individual
resources as well as averages. An unavailable metric is unknown, not zero. [S03]

Construct the inventory for this deployment rather than copying a universal
dashboard. It may include individual CPUs, memory capacity and bandwidth,
filesystems, block devices, NICs, container quotas, connection pools, executors,
and bounded application queues. For each entry record the actual capacity,
measurement interval, metric meaning, and responsible component.

Do not use a universal utilization threshold as a diagnosis. Two resources at
similar reported utilization may have different queueing behavior, parallelism,
service-time variability, or limits. Identify the limiting mechanism with a
controlled comparison; resizing everything simultaneously prevents attribution.

## Choose the next measurement from the question

| Question | Next evidence | Common interpretation error |
|---|---|---|
| Is the critical work waiting to run? | Thread scheduling delay, effective CPU limits, queue timing | Treating low host-wide CPU as available container capacity |
| Is CPU work expensive? | CPU seconds per valid operation, sampled stacks, focused counters | Interpreting a wide frame as elapsed request time |
| Is a lock on the critical path? | Contention duration, holder stacks, ownership pattern | Assuming lock-free replacement will be faster |
| Is memory the limit? | Working set, allocation/retention, pressure, traffic, locality | Treating every cache miss or large RSS as the same problem |
| Is a dependency the limit? | Client queue, connection setup, remote span, timeout outcomes | Blaming the network for time spent in an application pool |
| Is the benchmark valid? | Generator and target profiles, achieved arrivals, output checks | Assuming a stable timing means the intended work ran |

A flame graph aggregates stack observations; its horizontal arrangement is not
a chronological trace. Verify symbols, unwind quality, event type, sampling
loss, and profiling overhead before interpreting it. Resolve inlined or async
frames with a tool that supports the runtime, rather than guessing from names.
[S07]

## Actively observe the benchmark

Active benchmarking means observing the system while the benchmark executes,
including the benchmark implementation and its limiting resources. A throughput
result can measure the generator, a cache shortcut, or an error path instead of
the intended operation. [S06]

For this skill, require a lightweight diagnostic run proving that requests reach
the intended path and output is valid. Check that the generator can sustain the
arrival schedule, record errors/rejections, and inspect both warm and cold modes
when relevant. Then repeat final timing without expensive instrumentation.
Statistics cannot repair a benchmark that measures the wrong operation.

## End the investigation with a decision

Compare one candidate at a time against the preserved baseline. An experiment
that reduces queueing but raises memory can still be useful, but only inside the
explicit budgets. Re-profile after a successful change: the bottleneck can move.
Report a supported mechanism, the evidence against alternatives, and the
remaining unknowns. When access is limited, return the next discriminating
experiment rather than labelling a hypothesis as a root cause.
