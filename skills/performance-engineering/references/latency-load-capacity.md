# Latency, load, capacity, and recovery

Read for services, interactive applications, shared executors, and pipelines with
queues. Source IDs resolve in [sources.md](sources.md). Use
[the load-test plan](../templates/load-test-plan.md) to make the experiment
repeatable. Mathematical examples below are derived illustrations, not observed
results or prescribed production thresholds.

## Name the operation and its clocks

Define when an operation is offered, admitted, starts executing, finishes work,
and becomes usable by its consumer. A request may pass through several queues.
Keep enough timestamps to distinguish load-generator lag, admission delay,
execution, dependencies, and delivery without double-counting overlapping spans.
Track offered rate, admitted rate, completion rate, valid successful goodput,
rejections, timeouts, cancellations, and work still in flight. User-facing
latency, traffic, errors, and saturation answer different questions. [O06]

A result that completes an invalid output faster is not a performance win. Nor
is a service faster merely because it rejects expensive requests. Preserve the
input mix and output quality, and account for failures separately from the
successful-request distribution. Define the denominator of every rate.

## Keep distributions and cohorts intact

Store histograms or raw observations with counts, units, bounds, and the test
window. Report useful quantiles together with error rates and enough sample
information to judge tail stability. Break out workload size, region/device,
cache state, tenant skew, and other relevant cohorts; aggregate improvements can
hide harm to a required cohort.

Do not average per-instance p99 values. Merge compatible histogram observations
or counts first and compute the quantile for the combined distribution. Bucket
resolution limits accuracy; summaries with already-calculated quantiles cannot
generally be combined that way. An SLO threshold count may be more directly
useful than an interpolated percentile. [O04]

A percentile of batch-average timings is not the percentile of individual
requests. A timed-out request has an incomplete completion time, not zero
latency; keep its failure/deadline outcome visible. Do not silently drop it or
present its timeout duration as an exact eventual completion time. When comparing
tails across runs, use suitable request-level or repeated-run analysis, not the
bundled scalar paired-ratio utility as an automatic p99-certification tool.

## Match the load model to the question

A closed workload waits for work to finish before the same client issues more.
An open workload schedules arrivals independently of response completion.
Closed-loop feedback can reduce offered load during a stall and conceal the
experience of an external arrival stream, often called coordinated omission.
Neither model is universally correct: state which real traffic it represents.
[O07]

For an arrival-rate test, preserve the planned schedule and record dispatch lag,
missed/dropped iterations, generator capacity, and actual arrivals. A configured
arrival rate is not proof that it was achieved. Bound generator concurrency and
memory; a generator that cannot meet the schedule invalidates that portion of
the intended experiment. Analyze it rather than increasing resources blindly.
Profile the generator as well as the target. [S06]

Use a small correctness-oriented warm-up, then a predetermined measurement
window. Include representative distributions of inter-arrival times and request
costs, not only uniformly spaced equal-sized requests. Fix the comparison's
load, resource budget, data, and semantics. A saturation sweep is a different
experiment from an A/B comparison at one arrival rate.

## Model queueing without overclaiming

For a stable flow and a consistent boundary, Little's law relates long-run
averages: `L = lambda * W`, where `L` is work in the system, `lambda` is its
throughput, and `W` is its mean residence time. The cited queueing notes provide
the model; the examples and operational deductions below are this skill's.
It is not a p99 formula or a way to choose a thread count. Use the flow crossing
the chosen boundary, including applicable failed completions; do not multiply
an offered rate that includes rejections by admitted-request residence time.
[Q01]

At 400 requests/s and 0.05 s mean residence, the average in-flight work is 20.
If residence rises to 0.20 s at the same stable throughput, it becomes 80. The
extra work can be queued, waiting remotely, or executing; it is not necessarily
80 runnable threads. With a growing unbounded backlog, report transient arrival,
completion, and queue behavior instead of pretending the system is in steady
state.

For intuition only, an M/M/1 model assumes Poisson arrivals, independent
exponential service times, one FCFS server, unlimited waiting space, no abandonment,
and utilization `rho = lambda * S < 1`.
Its mean response time is `R = S / (1 - rho)`. With mean service `S = 5 ms`,
100 arrivals/s gives `rho = 0.5` and `R = 10 ms`; 180 arrivals/s gives `rho = 0.9`
and `R = 50 ms`. Production batching, caches, multi-server pools, and correlated
bursts need different models or measurements. Do not turn this illustration
into a universal utilization target. [Q02]

When a request waits for all `n` independent dependencies and each exceeds a
threshold with probability `p`, elementary probability gives
`P(any exceeds) = 1 - (1-p)^n`. At `p = 0.01` and `n = 50`, this is about 39.5%.
This derived example explains why fan-out merits a tail experiment; independence
is often unrealistic, and the formula does not predict a deployed service's p99.

## Find useful capacity, not the largest number on a chart

Sweep offered load through realistic operating points and past the point where
latency or errors breach the contract. At each point record achieved arrivals,
goodput, response distribution, errors, queue lengths/bytes, CPU, memory, and
limiting-resource evidence. Define usable capacity as the range satisfying the
specified budgets, not the peak completions before collapse.

Test a plateau long enough to expose the mechanism being studied. Do not infer
headroom from an isolated quiet interval. Correlate the knee in the load/latency
curve with resource or scheduling evidence, and repeat enough runs to separate
noise from behavior. Report the workload distribution and configured resources
alongside every capacity claim.

## Bound overload and retry amplification

Bound queues in both items and bytes, cap in-flight work, and specify admission,
backpressure, rejection, deadlines, and cancellation behavior. A queue can delay
failure while making all requests miss their deadlines. Protect useful work
rather than maximizing attempted work. Retries can amplify overload; admission
control and load shedding are application decisions, not free optimizations.
[O08]

For this skill, require an explicit retry owner, maximum attempts, deadline
budget, eligible errors, and idempotency contract. Include retries in offered
load and resource accounting; define any backoff/jitter policy deliberately.
Cancel work no longer needed when it is safe to do so, including queued tasks
and losing speculative requests. Verify that cancellation releases scratch,
permits, connections, and result buffers.

Batching trades setup amortization against time waiting for a batch. Test both
size and maximum-wait controls, including sparse traffic. Parallelism can reduce
service time while increasing contention, retained memory, and queue delay.
Choose worker and queue limits from measurements and budgets, not core count
alone. See [parallelism.md](parallelism.md).

## Test aging and recovery, not only the initial plateau

Include steady traffic, expected peak, burst, overload, soak, degraded dependency,
and recovery phases when relevant. A soak should cover the mechanisms suspected:
cache eviction, allocator retention, log rotation, scheduled cleanup, connection
turnover, or data growth. Explain the chosen duration; no fixed duration proves
all long-term behavior.

After overload or a dependency slowdown, return to the original offered load.
Measure queue-drain time, time to restore latency/error budgets, retained memory,
retry volume, and starvation. A design that needs a restart to recover has not
passed a recovery requirement. Degraded-service tests require authorization and
isolation; never induce production failures merely to complete this checklist.
