# Rust implementation guide

Source IDs resolve in [sources.md](sources.md). The companion crate has no
third-party dependencies. Its validation record distinguishes source review
from actual compilation and execution.

## Preserve ordinary Rust first

Use borrowed slices for read-only inputs and explicitly disjoint mutable output.
Validate lengths once before a loop. Keep iteration regular and operations
visible to the optimizer. Safe iterators and indexing are not inherently slower
than pointers; inspect the optimized hot path rather than judging syntax.
LLVM performs loop and straight-line vectorization when legal and profitable.
[T01, R03]

```rust
/// Explicit wrapping arithmetic; rejects unequal lengths instead of truncating.
pub fn affine(input: &[u32], output: &mut [u32]) {
    assert_eq!(input.len(), output.len());
    for (dst, &src) in output.iter_mut().zip(input) {
        *dst = src.wrapping_mul(3).wrapping_add(1);
    }
}
```

`zip` alone silently stops at the shorter side; the assertion is part of this
example's contract. Use `chunks_exact`/`chunks_exact_mut` for full blocks, then
process remainders explicitly. Do not hide truncation behind a performance API.
Use an error result instead of a panic when that is the repository's policy.

`#[inline]` is a hint; blanket `#[inline(always)]` can increase code size and
hurt instruction-cache behavior. Reserve forced inlining for a demonstrated
code-generation requirement, including a library's documented SIMD wrapper
requirements. Generic specialization can remove dispatch but also multiply code.
[R03, R07]

## Allocation and ownership

`Vec::with_capacity(n)` reserves storage but creates no initialized `T` elements;
its length is zero. A zero-size request or zero-sized element type need not
allocate heap storage. Spare storage is not a collection of readable `T` values.
`clear()` removes elements but retains allocation capacity. `reserve(additional)`
and `try_reserve(additional)` interpret the argument relative to **length**, not
capacity. Do not pass `desired_capacity - capacity` as though it were relative to
capacity. [R01]

For a caller-owned reusable output, reserve any required space before clearing
when allocation failure must leave the previous output intact. The example
`map_reusing` demonstrates this policy. Dropping old elements and calling a
fallible user closure can introduce additional panic/partial-output semantics;
this example deliberately uses simple `u32` arithmetic. [R01]

Prefer initialized safe buffers until measurement identifies initialization as
material. With `MaybeUninit<T>`, prove which elements are initialized and when
the logical length becomes valid. Never create `&T`, read a `T`, or expose a slice
of `T` over uninitialized storage. Include error and panic cleanup, and drop only
initialized elements. `set_len` does not initialize memory. [R02]

Do not assume `Box`, `Arc`, cloning, iterator collection, strings, formatting, or
trait objects are allocation-free; inspect the concrete operation and capacity.
Conversely, a closure or an iterator adapter does not imply a heap allocation.
Measure allocations and ownership transfers at the public API boundary.

## Choose a SIMD layer deliberately

| Layer | Suitable use | What must be verified |
|---|---|---|
| Scalar Rust + LLVM | Simple regular loops | Generated code, aliasing, numerical legality |
| `fearless_simd` | Portable generic kernels and runtime-selected backends | Locked API, dispatch boundaries, supported operations, documented inlining |
| `wide` | Convenient fixed-width vector values | Target lowering, type width, integer/float semantics, dispatch strategy |
| `pulp` | Runtime architecture dispatch and generic SIMD kernels | Target support, backend capabilities, locked API |
| `std::simd` | Portable vector API where nightly is permitted | Toolchain pin, feature gate, supported lane counts and operations |
| `std::arch` | A measured gap requiring target intrinsics | CPU/OS feature detection, safety proofs, fallback and target tests |

As checked on 2026-09-07, the official `std::simd` documentation still marks it
nightly-only under `portable_simd`. Recheck this before changing a project's
stable-toolchain requirement. Portable semantics do not promise a single native
instruction or the widest available register. [R04]
See the [re-verification checklist](sources.md#time-sensitive-claims-to-re-verify)
for this check and other version-sensitive guidance.

`fearless_simd` documents a `Level`/dispatch mechanism and generic SIMD kernels;
`wide` presents fixed-width types; `pulp` documents runtime dispatch through an
architecture abstraction. These are different design choices, not benchmark
rankings. Confirm the repository's locked versions before writing code. [R07,
R08, R09]

### Library integration procedure

Read `Cargo.toml`, `Cargo.lock`, the MSRV, and target policy. Resolve the exact
installed crate's documentation or local source. Build one small compile test
that loads a full block, performs the required operation, stores it, and handles
a tail. Verify mask selection, integer widening, reduction, and gather semantics.
Do not invent method names by analogy with a different SIMD crate.

Dispatch once per complete operation or sizable batch. Keep the generic kernel
and helpers inlinable as required by the chosen library. Inspect representative
backends separately: a legal gather or shuffle can scalarize. Never use one x86
assembly listing as evidence for Arm code generation. [R03, R07, R09]

## Intrinsic boundary

Expose a safe function accepting slices. Keep target-feature functions private.
On x86, call AVX2 code only after an established feature detector reports support;
AVX2 does not imply unrelated FMA or BMI requirements for your whole algorithm.
Do not compile the entire distributable binary for the developer's native CPU
and then expect runtime dispatch to restore portability. [R03, D01]

For each unsafe block, document supported features, pointer provenance, the full
range of readable/writable elements, alignment, and aliasing. A final incomplete
vector is not readable just because the following virtual page exists. Prefer a
scalar tail initially. The companion byte-search code demonstrates SSE2/AVX2
and a guarded AArch64 NEON implementation; see its actual test coverage.

## Inspect and test

Useful starting commands, adjusted to the repository's toolchain:

```sh
cargo test --all-targets
cargo test --release --all-targets
cargo rustc --release --lib -- --emit=asm
# Optional only when a nightly/Miri setup is explicitly available:
# cargo +nightly miri test
```

Miri, sanitizers, and cross-compilation provide different coverage. Some target
intrinsics are not supported by an interpreter; a skipped intrinsic test is not
a pass. Native target execution is required to claim that backend was tested.
Profile release artifacts, not Miri or sanitizer builds. [R03, R06]

Tune LTO, codegen units, PGO, and panic strategy only as explicit experiments.
Cargo profile settings affect builds and semantics; changing panic behavior is
not a harmless benchmark switch. Keep debug assertions and overflow behavior
consistent with the intended public contract. [R06]
