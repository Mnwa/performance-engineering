# Fast by Default: prevent performance decay

Use when designing new software, reviewing a feature, or establishing ongoing
performance checks. Source IDs resolve in [sources.md](sources.md).

## Source boundary

Den Odell's public model treats performance as a requirement across architecture,
development feedback, budgets, complete user flows, production evidence, shared
ownership, and continuing maintenance. Its cycle is Measure, Build, Own, and
Maintain and Refine; its practical steps are Architect, Implement, Verify,
Observe, and Refine. [F02]

The publisher's listing for *Fast by Default: Practical Performance Engineering*
was early access on 2026-09-06, with eight of twenty chapters available and an
estimated Spring 2027 publication. The full book text was not accessed for this
update. The publisher mentions a System Paths framework, but this skill does
not invent its taxonomy or claim that the following templates reproduce it.
The procedures below are this skill's original operational adaptation. [F01]

## Architect: specify the fast path before implementation

Create a [performance budget](../templates/performance-budget.md) before choosing
optimizations. Identify the useful operation and the exact completion condition:
for a library, valid output delivered to its caller; for a pipeline, output
consumed or persisted under its durability contract; for an interactive flow,
the point where the result is usable, not merely when an internal function ends.

Map dependencies and handoffs for that operation. For each stage, record data
volume, how often it runs, ownership/lifetime, concurrency, and who can block
whom. Identify repeated serialization, full-data passes, N+1 calls, redundant
queries, and startup work unrelated to the requested result. A stage count or
byte count is a review aid, not proof of the resulting latency.

Allocate absolute budgets for latency, CPU, memory/retention, and output quality
as appropriate. A stage budget is not an excuse to sum independent p99s and call
that the end-to-end p99. For sequential deterministic planning, stage limits can
help reserve headroom; validate the full distribution under realistic load.
Record assumptions about cache misses, data growth, worker counts, and dependency
slowness explicitly instead of hiding them in the implementation.

Avoid premature instruction tuning, but do not postpone structural decisions
that are expensive to undo: data layout, ownership, query shape, API granularity,
bounded queues, streaming versus materializing, and redundant copies. Start with
a simple correct implementation and retain its correctness oracle.

## Implement: make the efficient use case the easy one

Design APIs that express work and lifetime clearly. Offer bounded reusable
scratch where it is useful, avoid forcing a temporary allocation at every layer,
and allow bulk operations when the caller naturally has a batch. Do not force
all callers to pay precomputation or maximum-size retention for a rare case.
Use narrow fast paths with a general fallback and a measured dispatch threshold.
These are design hypotheses to benchmark, not universal rules.

Treat a new dependency as runtime work, initialization, code size, and maintenance
as well as source-code convenience. Check whether it sits on the critical path,
adds hidden threading, expands payloads, or duplicates work already done nearby.
Prefer a maintained standard implementation unless a measured need justifies
specialization. Never remove input validation, authentication, or durability to
make the fast path appear cheaper.

When adding a cache, write the miss path first: key correctness, invalidation,
size and retention bounds, eviction, concurrent fills, and failure behavior.
Measure hit, miss, cold-start, and burst modes independently and in the production
mix. A higher hit rate is not enough if entries become stale, misses stampede a
dependency, or memory exceeds budget. Compare the entire lookup/fill/lifetime
cost against recomputation.

Keep lightweight local performance feedback close to a changed path: reproducible
representative fixtures, commands, input hashes, and a small benchmark subset.
Use heavyweight tracing or sanitizers for diagnosis/correctness separately from
uninstrumented timing. Label unexecuted target paths rather than claiming
portability from source inspection alone.

## Verify: protect an absolute requirement and a relative baseline

Use both an absolute budget and a relative regression policy. Relative-only
checks can accept a sequence of small slowdowns; absolute-only checks can miss a
large regression while spare headroom remains. Keep an approved release baseline
as well as a recent comparison, and version the workload and measurement method.
The skill's existing configurable `0.95` normalized-speedup gate is its own
policy, not a threshold from either book.

A recommended three-level arrangement:

| Stage | Checks | Failure handling |
|---|---|---|
| Local/PR | Correctness, algorithmic work/size checks, representative micro and end-to-end cases | Report effect and uncertainty; do not label missing or inconclusive evidence PASS |
| Controlled scheduled run | Larger workload/CPU matrix, load curves, tails, memory, soak/recovery | Compare per case and absolute budgets; investigate environmental drift |
| Authorized rollout/production | Real workload cohorts, valid goodput, tails/errors, resource/cost trends | Follow the pre-agreed rollback or mitigation decision; do not silently rebaseline |

These tiers are this skill's suggestion, not a demand to add every tool to every
project. Start with one important path and a trustworthy check. Enforce only
measurements with an understood noise floor. Use shared-runner results as
screening when their variance cannot support a narrow timing gate; rerun on an
appropriate controlled setup according to a predetermined policy, not until a
failing result happens to turn green.

A gate must name its metric, unit, boundary, workload, load, environment, minimum
evidence, uncertainty policy, owner, and outcome for missing data. Expensive
checks can be deferred to a defined stage, but their status remains pending or
unvalidated. An exception must have a reason, owner, expiry/review date, and
mitigation; changing the baseline is a reviewed action.

## Observe: use complete flows and actual workload cohorts

Connect a performance change to the operation's real outcome. Preserve request
correlation across workers/dependencies, measure the final consumer boundary,
and examine errors and saturation with latency. A server-side timing improvement
can be irrelevant to a user waiting on a different stage. [O06]

Compare relevant cohorts rather than one global average: input size, cache state,
region/device class, concurrency, and data skew. Keep production instrumentation
bounded and privacy-aware. Separate organic workload changes from changes in
software behavior; use a matched comparison where practical and state remaining
confounders. Do not claim a causal production gain from an unmatched before/after
chart alone.

## Refine: keep ownership and remove obsolete work

Assign an owner to each budget and benchmark corpus, not just to the profiling
tool. During recurring review, examine dependency upgrades, inactive feature
paths, stale cache policy, retained data, accumulating instrumentation, and
input-size growth. Recheck specialized thresholds on supported hardware and
compiler versions when those change.

After a successful optimization, remove superseded workarounds when safe, keep
its regression case, and document the mechanism and fallback. Delete speculative
complexity that failed to improve the objective. A faster but unmaintainable path
can decay as assumptions change; preserve evidence and a clear rollback path.

For a final decision use [performance-report.md](../templates/performance-report.md)
plus the budget/verification status. Report measured, derived, hypothesized, and
unvalidated items separately. Passing the package's correctness tests is not a
measurement that this process makes a user's application faster.
