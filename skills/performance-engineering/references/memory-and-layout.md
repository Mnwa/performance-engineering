# Memory and data layout

Sources resolve in [sources.md](sources.md). Optimize useful work per transferred
cache line before writing complicated prefetch code.

## Match representation to traversal

Array of structures (AoS) is convenient when each operation uses most fields of
one object. Structure of arrays (SoA) is a candidate when a hot loop scans a few
fields across many objects. Array of structures of arrays (AoSoA) tiles that
tradeoff. Measure conversion, extra allocations, and every important consumer,
not just the best-looking kernel. [A03]

For a hot record containing a key, count, flags, pointers, and descriptive data,
first ask which fields are read together. Split cold metadata, use compact
indices where ranges permit, and arrange contiguous storage for hot fields.
Do not force packing that creates invalidly aligned references. Shrinking an
index from 64 to 32 bits requires a capacity/range proof and an overflow policy.
[A11, A26]

Logical equality of representations is not enough: preserve stable handles,
iteration ordering, mutation semantics, and lifetime guarantees. Include the
migration/build cost when measuring an alternative index.

## Bandwidth versus latency

A sequential scan can issue many memory requests and approach a bandwidth limit.
A pointer-linked traversal may wait for each loaded address before discovering
the next one. Both can miss cache, but need different fixes. Candidate remedies
for dependent latency are compact nodes, index-based storage, batching
independent queries, and reducing levels of indirection. [A04, A27]

Use the smallest safe type when it meaningfully reduces traffic; wider
accumulators can remain in registers. Compression can trade decode work for
fewer transferred bytes. Measure decode throughput, random-access cost, and
whether the working set moves into a different cache level.

Estimate bytes for inputs, outputs, temporary arrays, write allocation, and
repeated passes. Fusing `map -> temporary -> filter -> temporary -> reduce`
can remove traffic and allocation, but a giant fused loop can increase register
pressure or inhibit a better specialized kernel. Compare both designs. [A23]

## Blocking and tiling

Choose a tile so the **combined** live inputs, outputs, scratch, and working
state fit the intended cache with headroom. Do not assign the entire nominal
cache capacity to one operand. Sweep tile sizes and shapes; cache associativity,
multiple workers, and other application state can matter. [A18, A28]

Separate cache blocking from register blocking. The former controls transfers;
the latter keeps independent accumulators and reused operands close to the
execution units. Matrix multiplication is the canonical example, but the same
questions apply to image transforms, dynamic programming, and batched scoring.
Start from a tuned library when it supports the needed semantics. [A18]

## Alignment and cache lines

Alignment can avoid split accesses and enable particular instructions, but it
also adds padding. Use legal unaligned operations when an API does not promise
alignment; prove bounds independently. Base-address alignment does not imply
that every subslice is aligned. Avoid casting an arbitrary byte slice into a
reference requiring stronger alignment. [A11]

A SIMD tail cannot read beyond an allocation merely because the unused lanes
are discarded later. Crossing into a guard page can fault; within-allocation
uninitialized bytes can still violate the language contract. Safe choices are a
scalar tail, a small initialized temporary, or a documented masked load with
all required pointer and lane preconditions satisfied. [R02, A22]

## Prefetch, stores, and pages

Try software prefetch only after demonstrating a latency bottleneck and a
predictable future address. Sweep distance; include instruction overhead and
cache pollution. It is often unnecessary for a regular stream and cannot make
an invalid pointer computation valid. [A29]

Non-temporal stores are candidates for large write-only streams not reused soon.
Check ISA alignment, ordering, and publication requirements. An ISA store fence,
where required, is not a substitute for language-level inter-thread
synchronization. Keep a normal-store path for small or soon-reused output.
[A30]

Large working sets can incur address-translation overhead. Huge pages may
reduce it, but allocation, compaction, fragmentation, and fault latency can
change. Linux supports configurable transparent-hugepage behavior; do not
change host-wide policy as an unmeasured default. Use controlled per-process
experiments where supported. [M05]

## Sharing and locality

Partition output and scratch so workers avoid writing the same cache lines.
False sharing can exist without a language data race. Pad selected hot metadata
only after inspecting real layout and target cache-line behavior; padding every
object can harm locality. NUMA first-touch and task migration belong in the
experiment on systems where they apply. [A31]

Reject a layout “win” that omits construction, hurts dominant lookups, or merely
shifts memory from tracked heap objects into an untracked arena. Report both
steady-state operation cost and lifecycle cost.
