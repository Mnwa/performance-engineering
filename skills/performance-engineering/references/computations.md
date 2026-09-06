# Computations, arithmetic, and numerical contracts

Sources resolve in [sources.md](sources.md). Most transformations below are
candidates, not unconditional substitutions. The histogram/logarithm design is
an original worked application of these principles.

## Remove work and expose invariants

Hoist repeated parameter validation, length checks, masks, scale factors, and
fixed divisors out of a hot loop when the contract permits. Fuse repeated
statistics over the same input when that removes a pass without causing spills
or changing required order. Reuse expensive derived metadata across queries,
but include construction and invalidation costs. [A12]

A specialization is worthwhile only if its startup/dispatch and code-size costs
are repaid. For setup cost `C` and per-item saving `d > 0`, a simple break-even
model is `n > C/d`. Measure the real crossover and preserve a generic path.

Do not compute a full sort when the caller needs only a minimum, top-k, or a
partition. Do not materialize output when the consumer only needs a predicate or
aggregate. These are interface/algorithm choices, not instruction tricks.

## Latency versus throughput

A loop with one dependent accumulator can be limited by the recurrence rather
than execution-unit throughput. Several independent accumulators can expose
instruction-level parallelism. Tune their count; excessive unrolling increases
register pressure, spills, and instruction footprint. [A10]

```text
a0 = a1 = a2 = a3 = identity
for each full block of four independent items:
    a0 = combine(a0, x0)
    a1 = combine(a1, x1)
    a2 = combine(a2, x2)
    a3 = combine(a3, x3)
result = combine the four accumulators, then handle the tail
```

This requires associative semantics or an approved change of evaluation order.
Unsigned wrapping sum is associative modulo its width; ordinary floating-point
sum is not associative. Saturating arithmetic also needs separate analysis.
Measure latency chains and independent-stream throughput separately. [A05, A08]

## Branches and eager selection

Use branches to skip genuinely expensive rare work. Consider masking or
selection when both alternatives are cheap and branch outcomes are difficult
to predict. A select generally chooses between already computed values; it does
not promise lazy evaluation. Converting a branch into two expensive computations
can be a regression. [A09]

A scalar branch around an entire vector block can be useful: process an all-zero
or all-small block cheaply, otherwise take a general path. Measure how often a
block is mixed, not just the overall fraction of rare elements.

Source-level branchlessness is not a constant-time security proof. Secret-indexed
lookup tables and data-dependent memory access can leak even without branches.
Keep security-sensitive code under its established threat model and review.

## Integer arithmetic

State input range and output range before narrowing a type, removing a check,
replacing a division, or accumulating vector lanes. Promote before multiplying
when the mathematical product needs more bits. Prove counter bounds from maximum
items per lane between flushes. Do not “fix” debug overflows by measuring release
builds that wrap unintentionally.

Constant divisors often allow multiply/shift lowering. For a runtime divisor
reused many times, a proven divider with precomputed metadata is a candidate;
libdivide supports this use case. Include setup and handle zero, one, signed
minimum divided by minus one, rounding direction, and exactness. Do not invent
a general magic multiplier without a proof. [A07, N03]

The rewrite `x / 2^k -> x >> k` is straightforward for nonnegative/unsigned
integers under the appropriate shift range. Signed negative division and
arithmetic right shift need not round in the same direction. Similarly,
`x % m -> x & (m-1)` requires a positive power-of-two modulus and suitable
unsigned semantics. Language and ISA shift edge cases differ.

For bit-oriented workloads, consider bitsets and word-wide operations before
SIMD. Preserve trailing-bit masks and empty-input semantics. A scalar population
count instruction is not available merely because an unrelated SIMD extension
is available; verify feature requirements.

## Floating-point contract

Specify absolute/relative error, optionally ULP error, monotonicity, handling of
zero, negative input, infinities, NaNs, and subnormals, plus whether bitwise
reproducibility is required. Record FMA contraction and reduction order. An FMA
rounds a multiply-add differently from two separate operations; “more accurate”
does not mean “identical to the old output.” [A08, A13, T03]

Use `abs(a-b) <= atol + rtol * abs(reference)` only when that metric fits the
problem and special values are handled separately. Relative error is unsuitable
near zero. Machine epsilon by itself is not an application tolerance.
A compiler's fast-math mode can change assumptions about NaNs, infinities,
signed zero, and reassociation; do not enable it globally as a generic speed flag.
[T03]

Use compensated or pairwise accumulation when accuracy requires it. A wider
accumulator can be a better tradeoff than a more elaborate approximation.
Measure input conversion and lane-width changes, not just multiply throughput.
Correct-rounding guarantees for basic operations do not automatically extend to
an arbitrary platform's transcendental library function.

## Reciprocal refinement and polynomial evaluation

For a suitable positive input and an adequate starting estimate `r`, reciprocal
Newton refinement uses `r <- r * (2 - x*r)`. Reciprocal-square-root refinement
uses `r <- r * (1.5 - 0.5*x*r*r)`. These are algebraic iterations, not universal
IEEE replacements: check starting approximation, subnormals, overflow/underflow,
special values, and the accuracy after each iteration. Benchmark against actual
hardware divide/sqrt and a trusted vector math library. [A14, D02, N01]

Horner evaluation minimizes a straightforward polynomial's arithmetic and
storage but creates a dependency chain. Estrin-style grouping exposes independent
subexpressions at the cost of powers/temporaries. Compare scheduling and spills.
Use generated, versioned coefficients with a reproducible domain/error test;
never insert unexplained constants and label the result “accurate.”

For general `log`, `exp`, and trigonometric functions, prefer established vector
math implementations where they meet the contract. SLEEF and Arm's optimized
routines are implementation/reference options, not promises of identical
accuracy or behavior across all functions and builds. [N01, N02]

## Worked design: histogram score and hybrid log₂

Suppose the operation is

```text
score = (log2(N) + a) * N + b
        - sum over bins c[i] * (depth[i] + log2(c[i]))
```

First define `N`, including sampling and empty-input behavior. Do not silently
replace a sampled total with full input length. Define the `c=0` contribution
as zero directly; evaluating `0 * log2(0)` can produce NaN. Specify whether the
contract is a mathematical score, reproduction of an existing `fast_log2`, or
only a final decision. Those are different contracts.

### Candidate designs

Compare scalar library log₂, scalar lookup with a large-value fallback, pure
vector approximation, vector table gather, and a block-hybrid. Include histogram
construction, clearing, conversions, and reduction in the end-to-end experiment.
A 256-entry `f64` table holds 2048 data bytes; that arithmetic does not prove a
lookup is cheaper than a short polynomial. [A12, A16]

Measure the count distribution and the distribution **by SIMD block**. If a rare
large count contaminates most blocks, the all-small fast path may seldom apply.
Do not force sparse exceptional lanes through a full expensive vector path
without comparing a scalar fixup strategy.

### Safe hybrid pseudocode

```text
c = load complete block of counts
positive = (c != 0)
small = (c < K)                    # require K >= 2
index = min(c, K - 1)              # sanitize BEFORE every table access

if all(small):
    value = lookup(table, index)   # table[0] is a defined neutral value
else if none(small):
    value = approximate_log2(max(c, 1))
else:
    # Both computations may execute. All operands must be independently safe.
    from_table = lookup(table, index)
    from_math = approximate_log2(max(c, 1))
    value = select(small, from_table, from_math)

term = select(positive, widen(c) * (widen(depth) + value), 0)
accumulate term into independent accumulators
```

Compare the mixed-block case with extracting only exceptional lanes. Ordinary
NEON table shuffles do not make a 256-entry `f64` gather free; lookup width,
byte-versus-element semantics, instruction count, and register pressure matter.
The actual kernel may prefer scalar L1 lookups feeding vector arithmetic.
[A16, D02]

### Positive integer range reduction

For nonzero `u32 c`, choose `k = floor(log2(c))` and `m = c / 2^k`, so
`m in [1,2)` and `log2(c) = k + log2(m)`. Conversion to `f64` can represent every
`u32` exactly; conversion to `f32` cannot represent all integers above `2^24`.
Count conversion error in the final bound. SIMD leading-zero operations and
unsigned conversions have different implementations across ISAs. [A13]

One transparent teaching approximation uses

```text
z = (m - 1) / (m + 1)
log2(m) ≈ (2 / ln(2)) * z * (1 + z²/3 + z⁴/5 + z⁶/7 + z⁸/9)
```

This follows the odd-power series of `2*atanh(z)`. Since `0 <= z < 1/3`, the
real-arithmetic truncation remainder after the `z^9` term is bounded by

```text
(2 / ln(2)) * |z|^11 / (11 * (1 - z²)).
```

Derivation: every omitted denominator is at least 11, and the remaining powers
are bounded by a geometric series. This is **not** the floating-point error
bound of a compiled kernel: division, coefficients, conversion, and accumulation
add errors. The included scalar example is transparent and testable, not a
claim to beat a vector libm. A tighter interval near one can reduce the needed
polynomial degree, but adds range-reduction work.

### Decisions near a threshold

For errors `|log2_hat(c[i])-log2(c[i])| <= eps[i]`, a conservative mathematical
score-error budget includes

```text
E >= N * eps_N + sum(c[i] * eps[i]) + E_other_arithmetic.
```

If testing `score >= 0`, then `score_hat - E >= 0` proves acceptance and
`score_hat + E < 0` proves rejection; otherwise use the reference path. The
inequalities deliberately differ at equality. Include errors in constants,
products, accumulation, and approximated total terms. Require a valid bound,
not just the largest observed error in a random test.

For bit-for-bit compatibility with an old approximate scalar routine, the
bound must be relative to **that routine**, including its evaluation order;
closeness to mathematical log₂ alone is insufficient. Without a proven bound,
use an explicitly approved approximate contract and report decision-flip tests.
