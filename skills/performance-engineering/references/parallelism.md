# Parallelism, allocation, and ownership

Apply this after identifying the serial bottleneck. Source IDs resolve in
[sources.md](sources.md). More workers can amplify memory traffic, retained
scratch, contention, and queueing rather than improve useful throughput.

## Design units of work

Partition input and output so each task owns a disjoint region. Keep shared
metadata read-only where possible; merge local results explicitly. For variable
output sizes, either compute output offsets in a prior pass or use bounded local
buffers and a controlled merge. Include the additional passes and storage in the
benchmark. [A19, A31]

Choose granularity using measured scheduling and setup overhead, not a fixed
universal chunk size. Tasks must be large enough to amortize dispatch but small
enough to balance skewed work. Benchmark both uniform and skewed input costs.
Avoid recursive unbounded spawning and nested independent thread pools.

Separate algorithm state from execution policy when a library must integrate
with different callers: define owned or scoped work items, explicit result
storage, and a completion mechanism rather than assuming a particular global
executor. Scoped borrowed tasks and `'static` spawned tasks have different
lifetime requirements. Do not create dangling borrows merely to accept every
spawner shape.

## Bound concurrency by memory as well as cores

Estimate a conservative memory budget:

```text
peak_live ≈ shared_read_only + queued_input + queued_output
          + active_workers * per_worker_scratch + merge_storage
          + allocator_slack + safety_margin
```

This is an accounting model, not a guarantee of measured RSS. Scratch capacity,
allocator retention, and delayed consumer progress can dominate. Limit in-flight
tasks and queue bytes, not only worker count. Release or trim oversized scratch
using a measured policy after a large request burst. [M02, M03]

A per-worker cache needs a process-wide budget. “Each worker retains at most one
buffer” is insufficient if each buffer may grow without bound or worker count
is uncontrolled. Measure cross-thread deallocation, ownership transfer, and
cancellation cleanup. Never hide per-thread memory by reporting only one worker.

## Remove shared hot writes

Use local counters/histograms and a later reduction when that preserves the
contract. Avoid adjacent hot fields written by different workers; false sharing
occurs when logically distinct writes contend through shared cache-line state.
Do not hardcode a universal cache-line size as a language portability guarantee.
Padding also increases the footprint and must be measured. [A31]

Atomic instructions and lock-free structures are not automatically low latency.
Contention, retries, reclamation, fairness, and memory ordering are part of the
algorithm. Do not weaken synchronization without a memory-model proof and
concurrency tests. SIMD stores and hardware store fences do not replace a valid
language-level synchronization protocol.

## Locality and scaling

Keep producer/consumer ownership and allocation placement compatible with the
actual traversal. On NUMA machines, first-touch and placement policies affect
which memory node serves work; OS policy and migration complicate the result.
Use platform measurements instead of assuming physical locality from the thread
that allocated a pointer. [M04, A31]

Measure 1, 2, 4, and further relevant worker counts until the objective stops
improving. Inspect bandwidth saturation, loaded latency, allocator contention,
false sharing, and shared queue pressure. Retain a single-worker result: it
separates a kernel improvement from added resources. [A23, A04]

For floating-point reductions, changing task boundaries changes reduction order.
Select deterministic ordering or a documented error tolerance. Preserve stable
ordering and tie policy in merges when the API requires them. Cancellation and
partial failure must reclaim buffers and leave outputs in a defined state.

## Acceptance

Report throughput, per-request latency under realistic offered load, total CPU
consumption, peak and post-burst memory, worker count, queue limits, and failure
behavior. An unbounded queue can make throughput look healthy while user latency
and memory become unacceptable. Include the consumer and merge phase in the
end-to-end test; workers finishing quickly is not the completed operation.
