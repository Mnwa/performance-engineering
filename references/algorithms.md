# Hardware-aware algorithm patterns

Select the algorithm before selecting the instruction. Asymptotic complexity,
input distribution, working-set size, reuse, and setup cost all matter. Source
IDs resolve in [sources.md](sources.md).

## Selection table

| Required result | Baseline to retain | Alternatives to evaluate | Main trap |
|---|---|---|---|
| One minimum or first minimum | Linear scan | Multiple accumulators; SIMD block minimum | Full sorting; changed tie policy |
| Small top-k | Scan plus bounded candidate set | Heap; selection then sort k results | Sorting all n values |
| Repeated lookup in immutable data | Sorted array / standard search | Batched search; Eytzinger or blocked tree layout | Ignoring layout construction and unused queries |
| Dense bounded-key counting | Direct histogram | Independent local histograms; blocked counting | Scatter conflicts; oversized counter array |
| General key counting | Standard hash map | Reserved map; sorted batch; compact keys | Weak hash under hostile inputs; hidden allocations |
| Membership in bounded universe | Direct scan / set | Bitset; sorted sparse vector | Dense storage for a sparse enormous universe |
| Prefix aggregation | Scalar prefix loop | SIMD block scan; hierarchical parallel scan | Cross-lane and cross-block carry errors |
| Repeated dense numeric operation | Simple loop / established library | Packing, tiling, fused kernels, SIMD | Conversion cost exceeds reuse benefit |
| Variable-length filtering | Scalar stable filter | Mask plus compaction; count-prefix-write | Out-of-bounds full-vector stores |

These are experiment candidates, not a universal ranking. Prefer standard
implementations until the profile justifies a specialized implementation.

## 1. Minimum and argmin

Specify whether empty input is invalid or returns no result; whether the first
or last equal minimum wins; and the floating-point NaN policy. For first argmin,
compare pairs using `(value, original_index)` order, or first determine the
minimum value and then locate its first occurrence. [A17]

An inexpensive safe SIMD design is to reduce each full block to a minimum,
compare it with the incumbent, and scan only a newly improving block for its
first equal element. Initialize the incumbent from actual input, not a sentinel
that collides with a legitimate maximum value. A block equal to the incumbent
cannot improve an earlier first index. Whether occasional scalar scanning is a
win depends on the distribution.

Multiple accumulators may break dependencies in scalar or SIMD code. Combining
only values and losing indices is insufficient. Equal values must retain the
correct index across vector lanes, blocks, and the final tail.

## 2. Search and immutable layouts

A pointer-based tree can spend most of its time awaiting dependent loads even
when total transferred bandwidth is low. A compact array and multiple
independent outstanding searches attack a different limitation than replacing
one comparison with SIMD. [A04, A20, A26]

For read-mostly data, experiment with sorted arrays, Eytzinger/breadth-first
layouts, or cache-blocked search trees. Measure build time, extra space, original
index recovery, duplicate handling, and the number of lookups needed to amortize
construction. Bulk queries can increase throughput while increasing the latency
of an individual query. Keep those metrics separate. [A20, A21]

Branchy binary search can exploit predictable query distributions; branchless
search can remove mispredictions but preserve a dependent address chain. Search
layouts and prefetch policies are hardware- and distribution-dependent. Always
include successful, unsuccessful, clustered, repeated, and boundary queries.
Do not assume a page-safe prefetch argument is a language-valid pointer. [A09, A29]

## 3. Histograms and counting

Begin with a direct histogram for a compact byte-sized domain. Clear it outside
or inside the timed region according to the actual API contract; preserve an
end-to-end result that includes reset work. [A10]

Independent histograms can reduce recurrence dependencies when repeated keys
otherwise increment the same counter. A simple four-way unrolled loop sends
input positions 0, 1, 2, 3 to four separate tables and merges them afterward.
This also multiplies the working set and initialization work, so it can lose on
short inputs. The examples include this design without claiming a speedup.

Parallel counting usually uses worker-local tables and an explicit merge. Prove
that each local counter and the final total fit their types. SIMD histogram
updates need conflict handling: repeated keys in one vector must all contribute.
A gather-add-scatter sequence that writes the same address multiple times does
not implement counting. See [SIMD](simd.md).

For very large sparse key domains, compare touched-index reset, generation tags,
compact sparse structures, sorting, and hashing. Include generation wraparound,
retained capacity, and the cost of reporting entries in the required order.

## 4. Prefix sums and compaction

A scan returns every prefix, not just one total. For a full SIMD block, perform
in-register shift-and-add stages, add the preceding block's carry, store valid
lanes, and propagate the last valid prefix. Instructions with 128-bit sublane
boundaries require explicit cross-sublane handling in a wider vector. [A19, A16]

For unsigned modular sums, reassociation preserves modulo arithmetic. For signed
checked or saturating arithmetic, and especially for floating-point sums, first
prove that the new evaluation order meets the contract. Do not silently change
an exception or overflow policy into wrapping.

Stable filtering can use three phases: count survivors per block, scan counts to
obtain disjoint output offsets, then compact and write survivors. This pays for
multiple passes but enables independent writes. A masked full-width store is
only safe when the instruction and API actually suppress invalid writes; a
regular store followed by a logical length update is not a substitute. [A22]

## 5. Dense numeric kernels

Prefer a maintained numerical library for a standard large matrix operation
unless constraints justify custom code. For a specialized kernel, select loop
order so the innermost loop traverses contiguous memory, block the working set,
and reuse loaded values through register tiles. [A18, A03]

Packing is additional work and storage. Measure pack-plus-compute for one-shot
operands, and amortized packing for reused operands. Tile sizes must fit the
combined input, output, and scratch footprint, not just one matrix. Larger tiles
and more accumulators can spill registers or evict useful cache lines.

Reduction order, fused multiply-add, and narrowed types change numerical
behavior. The mathematical operation being a matrix product does not by itself
permit arbitrary rounding differences. [A08, A13]

## 6. Parsing, bytes, and bitsets

Start from the existing standard/library byte search, equality, or copy routine
as a competitor, not only a deliberately slow hand-written loop. Vectorized
classification often works best as a cheap first stage that identifies candidate
bytes; scalar verification then handles variable-length grammar or uncommon
cases. Include malformed input and escapes, and never cross allocation bounds.
[A15, A22]

For bitsets, combine whole machine words or vectors, reduce popcounts using the
required supported ISA, and clear or mask unused tail bits. Keep bit ordering
and serialized byte order explicit. Dense bitsets are not automatically suitable
for sparse universes; account for zeroing and scanning empty regions.

## 7. Sorting and batching

Do not replace a comparator or unstable sort without defining equal-key behavior.
A stable output may be required even when all values compare equal. For a small
bounded domain, counting/radix approaches exchange comparison work for passes and
scratch storage; their value depends on key width, memory traffic, and input size.
For a small top-k or a single extremum, avoid sorting the entire input.

Batching can amortize allocation, dispatch, locking, and function-call overhead,
and can expose independent memory operations. It also adds buffering, latency,
and cancellation complexity. Bound the batch and report both batch throughput
and per-request latency. Algorithmic savings do not excuse an unbounded queue.

## Review checklist

Write the result contract and original-index/ordering semantics. Count passes,
bytes, allocations, and setup amortization. Retain the simple reference. Explain
which measured limitation the new algorithm attacks. Benchmark small inputs and
unfavorable distributions as well as the favorable large case. Reject a faster
kernel when its conversion or cleanup costs make the operation slower.
