# Allocations, initialization, and memory retention

The target is the cost of the complete object lifecycle, not the number of
`malloc` calls. Sources: [sources.md](sources.md), especially R01–R02 and M01–M05.

## Account for the entire lifecycle

Track requested bytes, allocator-rounded bytes when observable, live initialized
bytes, container capacity, allocator-retained memory, virtual mappings, resident
pages, and peak resident set separately. These are not interchangeable metrics.
A container can be empty while retaining a large buffer. A freed buffer can
remain with an allocator rather than immediately lowering RSS. [R01, M02]

Use the following diagnostic ledger, with measurements rather than a presumed
additive hardware model:

```text
reservation / allocation metadata
+ initialization and reset traffic
+ first-touch/page-fault work
+ copying / growth / relocation
+ synchronization and cross-thread ownership transfer
+ destruction / deallocation / purge work
+ long-term retention and cache/TLB footprint
```

Some costs overlap; do not add independently measured wall times as an exact
end-to-end prediction. Include p99 allocation latency and failure behavior where
the application needs them.

## Make ownership cheaper before replacing the allocator

Prefer borrowed input, caller-owned output, and worker-owned scratch at hot API
boundaries. Make capacity reusable across requests without making reuse
unbounded. Reserve a justified size once rather than growing one element at a
time; do not repeatedly call exact reservation for the next single item.
When the final size is unknown, use amortized growth with a measured retention
policy rather than repeatedly copying the whole prefix. [R01]

Useful API shapes are `process(input, output, scratch)` and a stateful worker
context whose temporary storage is reset between jobs. Put scratch behind an
owner that cannot be concurrently reused. Batch FFI or runtime crossings as well
as data allocations when call overhead is significant.

Avoid a hidden allocation in each iterator adapter, formatting operation,
string concatenation, boxed callback, or ownership conversion. Verify actual
behavior: an iterator is not inherently allocating, and a closure is not
inherently heap-allocated. Build an allocation profile instead of judging syntax.

Treat small-buffer storage as a tradeoff. It can avoid a heap request while
increasing every object's size, stack pressure, copy cost, and cache occupancy.
Bound stack scratch explicitly; large arrays and deep recursion can exhaust a
thread's stack. An arena fits grouped lifetimes, not arbitrary escaping objects.
Specify destruction, cleanup-on-error, alignment, and ownership rules before use.

## Safe reusable Rust output

```rust
use std::collections::TryReserveError;

pub fn map_reusing(input: &[u32], out: &mut Vec<u32>)
    -> Result<(), TryReserveError>
{
    // Reserve additional elements relative to len, not relative to capacity.
    // Failure leaves the old output intact because clearing happens afterward.
    let additional = input.len().saturating_sub(out.len());
    out.try_reserve(additional)?;
    out.clear();
    for &x in input {
        out.push(x.wrapping_mul(3).wrapping_add(1));
    }
    Ok(())
}
```

The safe loop establishes initialized elements normally. This is a concrete API
pattern, not proof that it beats `extend` or compiler-generated bulk code. Compare
assembly and measurements before using unsafe initialization. Rust's vector
capacity/growth and initialization contracts are documented in R01.

## Initialization is independent of allocation

Compare fresh zeroed storage with recycled dirty storage plus clearing, and with
storage whose contents will be completely overwritten. New anonymous mappings
have zero-content semantics, but allocation paths can return reused memory,
physical page commitment may be delayed, and writing still has a real cost.
Measure first reads and first writes; never describe OS zeroing as free. [M04]

If every output element is overwritten before any read, eliminate redundant
initialization through a language-supported safe construction pattern first.
Only use `MaybeUninit` or raw storage when the initialization proof is explicit.
The proof must cover exceptional exits, partially initialized objects, validity
of every `T`, and destructors. `set_len` before initialization, forming a normal
reference to invalid values, or reading spare capacity is not an optimization.
[R02]

Pooled bytes are not necessarily zero. Clearing a vector's logical length does
not erase sensitive data. Preserve isolation between requests and use an
appropriate secure-erasure mechanism when required; ordinary dead stores may
be removed. Do not use pooling to expose previous users' bytes. [R01]

## Pick a reset strategy from access density

**Dense reset.** Clear the entire fixed-size region. This is simple, sequential,
and often the right baseline for small histograms. Count its bytes and frequency.

**Touched-index reset.** Record each index when it first becomes active, then
clear only those entries. The list must contain an index once, not once per
update. Include list storage, extra branches, sparse writes, and iteration order
in the measurement. A 256-bin table may be too small to justify this machinery.

**Generation tags.** Store a generation next to a value. A mismatched generation
means logical zero; initialize on first touch. Every reader must implement this
rule. On generation rollover, perform a real reset or use a proven scheme that
cannot alias stale entries. Added tags may double traffic or worsen cache fit.

**Overwrite-before-read.** Reinitialize only the active prefix/blocks when the
algorithm proves the rest cannot be read. Changing a logical length alone does
not prove that a reused hash table or matcher has no stale reachable entry.

These are alternative designs to benchmark. The included histogram example
provides a simple dense/private baseline rather than assuming sparse reset wins.

## Bounded buffer pools

A pool needs all of the following: maximum total retained bytes, maximum entry
count, maximum per-entry capacity, a fit policy, release/eviction rules, and a
concurrency ownership model. Account using capacity in bytes, including checked
multiplication for typed elements; entry count alone does not bound memory.
Avoid caching exceptional giant requests indefinitely.

For a request `need > 0`, a useful candidate policy is:

```text
need <= capacity <= 2 * need
```

Implement it without overflow:

```rust
pub fn fits_within_double(capacity: usize, need: usize) -> bool {
    need != 0 && capacity >= need && capacity - need <= need
}
```

Short-circuit evaluation proves subtraction is valid. The zero-size policy here
is to bypass the pool. Test exact fit, exactly double, one above double, too
small, zero, and values near the integer maximum. This predicate is **not** a
complete pool policy.

This guard is wrong:

```text
capacity >= need && need < capacity * 2
```

For positive capacities it adds no useful upper-size constraint; the
multiplication can also overflow. Selecting the smallest eligible buffer does
not fix a missing oversize rejection when all retained buffers are enormous.

Use a size-class directory or a bounded linear scan depending on pool scale.
Benchmark pool hit rate, lookup time, lock contention, misses, and memory. On a
put, drop an entry exceeding the per-entry cap; evict according to a documented
policy until admitting the new entry respects the total budget. Avoid
shrink/grow thrashing on every request. Bound all worker-local pools globally:
`workers * per_worker_budget` is part of the application memory envelope.

## General-purpose allocator experiments

Choose between the system allocator and alternatives only after diagnosing the
allocation workload. TCMalloc's documentation distinguishes front-end caches,
transfer/central structures, and OS-facing back ends; local fast paths do not
mean the whole lifecycle is contention-free. [M03]

Mimalloc documents sharded free lists and configurable purging. Treat purge
settings as experiments: aggressive release can improve post-burst retention
while increasing later page-fault or reinitialization work. Check the deployed
version instead of copying a historical default. [M01]

Jemalloc exposes arenas, thread caches, decay/purge controls, and multiple memory
statistics. Use those to explain retention rather than interpreting process RSS
as the number of live application objects. More arenas or caches can trade
contention for memory. [M02]

Test realistic size/lifetime distributions, allocating and freeing on the same
and different workers, steady state, bursts, idle recovery, and production
concurrency. Preserve environment settings in results. Never advertise fixed
“direct-to-OS” size thresholds without checking allocator version and options.

## Memory acceptance checklist

The optimization must preserve allocation-failure behavior, initialization,
alignment, deallocation ownership, and request isolation. Require both peak and
post-burst measurements. A faster allocator-only microbenchmark is insufficient
when the new design retains more memory than the application's budget.
