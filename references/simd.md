# SIMD design and algorithm recipes

Sources resolve in [sources.md](sources.md). SIMD is a way of executing a suitable
algorithm, not a substitute for choosing one.

## Choose the implementation level

Start with a correct scalar implementation and an optimization-friendly loop.
Inspect compiler vectorization. Then evaluate a portable vector abstraction or
multiversioning library. Use architecture intrinsics when a measured hot path
needs a specific operation or lowering. Keep dispatch and fallbacks testable.
[A06, R03, T01]

Do not assume source vectors correspond one-to-one with machine registers.
A wide type can become multiple narrower vectors or scalar operations. Library
semantics may require extra work for floating-point minimum, masks, or casts.
Check the operations you actually use. [R04]

## ISA selection

| Target family | Relevant baseline/design distinction |
|---|---|
| x86 SSE/SSE2 | SSE includes packed single-precision floating point; SSE2 adds important integer and double-precision operations. Gate deployment requirements. |
| x86 AVX/AVX2 | AVX adds wider floating-point vectors; AVX2 supplies important 256-bit integer operations and gathers. AVX does not imply AVX2. |
| x86 optional extensions | FMA, SSSE3 byte shuffle, BMI, and AVX-512 subsets have their own requirements. Check every intrinsic. |
| AArch64 NEON | Usually 128-bit vector operations; use native reductions, interleaves, widening, and table operations where suitable. Check the actual target contract. |
| SVE/SVE2 | Design for scalable vector lengths and predicated tails; do not assume NEON or universal deployment. |

ISA names establish availability, not cycle counts. Verify instructions in the
vendor references and compiler target documentation. Wider execution can have
microarchitecture-dependent throughput, power, or frequency tradeoffs. [D01, D02]

For a portable binary, keep the generic build compatible with its lowest target.
Put optional ISA use inside gated implementations; globally enabling a feature
can contaminate the fallback. Dispatch once per substantial operation, not per
vector. A CPUID bit alone is not sufficient for all x86 execution-state checks;
prefer established compiler/runtime feature detection. [R03]

## Build the loop around its contract

Use four explicit phases: validate/dispatch, optional prefix, full-vector body,
and tail. State the width `W`, integer overflow policy, legal pointer range,
alignment, aliasing, and mask representation. When output can alias input,
prove that loads occur before the stores that would destroy needed values.

Use scalar tails by default. A masked **select** after a normal load does not
make an out-of-bounds load valid. A masked **load/gather** is different and must
be checked against its own memory-access and pointer-construction contract.
Do not assume inactive lanes suppress every floating-point exception. [A22, R03]

Benchmark small inputs separately: feature dispatch, constants, setup, and tails
can dominate them. Keep a measured scalar threshold rather than a universal
“SIMD starts at 32 bytes” rule.

## Expose auto-vectorization

Use straightforward counted loops or slice iteration, simple bounds, contiguous
memory, independent iterations, and small visible operations. Hoist invariants.
Remove opaque calls when they truly prevent optimization, but do not inline
large cold paths indiscriminately. LLVM may perform alias checks, epilogues,
reductions, and if-conversion according to legality and cost models. [A06, T01]

C/C++ aliasing qualifiers must describe real non-aliasing. Rust references must
remain valid; manufacturing overlapping mutable references to “help LLVM” is
undefined behavior. A high-level slice loop can remove checks naturally without
unchecked indexing. See the Rust reference for loop examples.

Compiler remarks to inspect with Clang:

```sh
clang++ -O3 -Rpass=loop-vectorize -Rpass-missed=loop-vectorize \
  -Rpass-analysis=loop-vectorize -c kernel.cpp
```

Validate flags against the installed compiler. Look for function calls inside
the vector loop, scalar extracts per item, spills, repeated horizontal
reductions, and unnecessary conversion chains. [T01]

## Recipe 1: map and fused map-reduce

Load contiguous lanes, apply elementwise operations, and either store or
accumulate directly. Eliminate a temporary only when the consumer does not need
it. Keep several vector accumulators for a reduction and combine them outside
the main loop. Benchmark the unfused version too when fusion increases register
pressure. [A05]

For `u32 -> u64` sum, widen **before** an addition can overflow. For byte sums,
widen periodically based on a proved maximum count per lane. For floating-point
dot products, choose whether FMA and reassociation are allowed. A different
reduction order can change both accuracy and downstream decisions.

## Recipe 2: byte search, equality, and mismatch

Broadcast the byte, compare full vectors, and test whether any lane matches.
On x86, a comparison plus byte mask can locate the first set lane with a
trailing-zero operation; guard a zero mask. On NEON, an any-match reduction plus
a scalar search inside only the matching block is a simple correctness-oriented
baseline; a tuned mask extraction can be a later experiment. [D01, D02]

For equality, combine full-vector differences and only localize a lane if the
caller requests an index. Preserve first-match ordering, endianness assumptions
in any word tricks, and byte offsets across tails. The included native example
implements safe complete-block loads and a scalar tail.

## Recipe 3: argmin/argmax

Choose a tie rule, including empty input and NaN behavior. A lane-wise
value/index pair needs lexicographic comparison in the final reduction: smaller
value first, then smaller index for first-occurrence semantics. Initialize from
valid data or carry a valid-lane mask; a sentinel alone can mishandle all-maximum
input. [A17]

An alternative is block minima: keep the first block with the global minimum,
then scan only that block for the first occurrence. This avoids a second full
pass and bounds final localization work. Compare monotonic and duplicate-heavy
inputs; a rare-update strategy may fail on descending data.

## Recipe 4: inclusive/exclusive prefix scan

For a full vector, use staged shifts/permutations and additions at distances
1, 2, 4, ... . Inject the carry from previous vectors and extract the last active
value as the next carry. Inclusive and exclusive definitions differ at the first
lane. [A19]

Many x86 byte shifts operate independently inside 128-bit sublanes, even with
256-bit types. Explicitly propagate cross-sublane carry. Test patterns where
only the last element of the lower sublane is nonzero. Unsigned wrapping scan
is a convenient exact baseline; floating-point scan changes evaluation order.

## Recipe 5: histogram construction

Naive gather-increment-scatter is wrong when lanes share an index: multiple
lanes can read the same old count and overwrite each other's updates. First
consider a few independent scalar histograms and a vectorizable merge. This
breaks hot-bin dependencies without relying on scatter semantics.

Alternative designs include lane-private tables, grouping equal keys, small
alphabet comparisons, or ISA-specific conflict handling. Include table clearing,
merge traffic, and cache footprint. Validate all-equal, two-symbol, uniform, and
highly skewed input. Choose counter width from maximum updates before merging.
This is an original recipe; its duplicate-index failure follows directly from
read-modify-write semantics.

## Recipe 6: sparse reductions and filtering

Compare a dense vector pass against an explicit active-index list. The latter
adds indirection and maintenance; it wins only when saved work repays those
costs. Detect all-zero or all-inactive blocks with a vector predicate when common.
Do not convert every mask to a scalar branch unnecessarily.

For compaction/filtering, compute a selection mask, obtain the selected count,
pack lanes, and write exactly within valid destination capacity. Preserve stable
order if promised. A full-width store after packing may overwrite the output
end or another worker's partition; use a documented compress-store or a safe
tail/temp path. Small-mask permutation tables need bounded, valid indices.
[A16, A22]

## Recipe 7: table lookup and classification

Use small in-register shuffles for compact byte/nibble mappings when the mapping
actually decomposes that way. A pair of 16-entry tables cannot represent an
arbitrary 256-entry function merely because the input splits into nibbles.
Distinguish byte shuffles, element permutes, and memory gathers. [A16]

For memory lookup, sanitize indices before the operation. Compare scalar L1
loads with gathers, and include index conversion, lane assembly, and table
pressure. See [computations.md](computations.md) for the mixed-block log₂ design.

## Recipe 8: bitsets and population counts

Use word-wise AND/OR/XOR to combine predicates and count only when needed.
Mask padding bits in the final word. For a SIMD popcount design, compare native
vector population count where available against lookup-based or carry-save
methods and a scalar hardware baseline. Do not assume an intrinsic named
`popcount` implies a single native vector instruction. [D01, D02]

## Recipe 9: matrix/tensor and transpose kernels

Use cache tiles, register-blocked accumulators, and a layout that exposes
contiguous loads. Include packing/transposition cost and reuse count. A faster
microkernel can lose on small matrices when packing dominates. Start from a
suitable tuned library; specialize only for demonstrated gaps. [A18]

## Recipe 10: batched search

Interleave independent queries to expose memory-level parallelism. Consider
SIMD comparisons inside compact nodes or across queries, but measure gathers
and control divergence. Batched throughput is not single-query latency.
Ordered-array binary search and static wide-node layouts remain baselines.
[A20, A21]

## Recipe 11: approximate math

Define domain, special values, conversion error, polynomial error, accumulation
error, and decision sensitivity before vectorizing. Evaluate polynomial-only,
lookup-only, and hybrid strategies. Handle invalid lanes before operations rather
than relying on a later select. Prefer an established vector math library when
it meets the contract. [N01, N02]

## Recipe 12: multiversioned kernels

Keep one public semantic contract and private target-specific functions. Test
scalar, baseline SIMD, optional wider SIMD, and automatic dispatch independently
on supporting hosts. Never bypass a CPU-feature check merely to increase test
coverage. Keep feature detection outside the repeated body and report which
implementation actually ran. [R03]

## Kernel validation matrix

Test zero and one element; all lengths through at least `2W+1`; long tails;
unaligned starting offsets; buffers ending at a protected page; all-zero,
all-equal, alternating, random, and extreme values. Include duplicate minima and
histogram collisions. For numerical kernels include domain edges and values
near decision thresholds. Cross-compile checks do not establish runtime
correctness or performance on another architecture.
