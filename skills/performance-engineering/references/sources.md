# Sources and provenance

Checked **2026-09-05**. Source IDs used throughout the skill refer to the entries
below. Exact instruction behavior, crate APIs, and compiler options must be
verified against the target and locked version used by a consuming project.

This is an original operational synthesis, not a reproduction of Algorithmica's
book. The examples, pool-fit predicate proof, histogram-score error-budget
application, suggested regression policy, report template, and verification
scripts were written for this package. Mathematical derivations are identified
as such; historical timings and speedup claims from sources are not transferred
to this package. Refer to upstream sources for their own authorship and licenses.

## Conceptual foundation: Algorithmica

Author: Sergey Slotin. Work: *Algorithms for Modern Hardware*.

| ID | Topic and primary source |
|---|---|
| A00 | [Book and contents](https://en.algorithmica.org/hpc/) |
| A01 | [Benchmarking](https://en.algorithmica.org/hpc/profiling/benchmarking/) |
| A02 | [Getting accurate results / measurement noise](https://en.algorithmica.org/hpc/profiling/noise/) |
| A03 | [Array of structs and struct of arrays](https://en.algorithmica.org/hpc/cpu-cache/aos-soa/) |
| A04 | [Memory-level parallelism](https://en.algorithmica.org/hpc/cpu-cache/mlp/) |
| A05 | [SIMD reductions](https://en.algorithmica.org/hpc/simd/reduction/) |
| A06 | [Auto-vectorization](https://en.algorithmica.org/hpc/simd/auto-vectorization/) |
| A07 | [Division](https://en.algorithmica.org/hpc/arithmetic/division/) |
| A08 | [Numerical errors](https://en.algorithmica.org/hpc/arithmetic/errors/) |
| A09 | [Branchless programming](https://en.algorithmica.org/hpc/pipelining/branchless/) |
| A10 | [Instruction-level throughput](https://en.algorithmica.org/hpc/pipelining/throughput/) |
| A11 | [Memory alignment](https://en.algorithmica.org/hpc/cpu-cache/alignment/) |
| A12 | [Precomputation](https://en.algorithmica.org/hpc/compilation/precalc/) |
| A13 | [IEEE 754](https://en.algorithmica.org/hpc/arithmetic/ieee-754/) |
| A14 | [Newton's method](https://en.algorithmica.org/hpc/arithmetic/newton/) |
| A15 | [SIMD intrinsics](https://en.algorithmica.org/hpc/simd/intrinsics/) |
| A16 | [Shuffling](https://en.algorithmica.org/hpc/simd/shuffling/) |
| A17 | [Argmin](https://en.algorithmica.org/hpc/algorithms/argmin/) |
| A18 | [Matrix multiplication](https://en.algorithmica.org/hpc/algorithms/matmul/) |
| A19 | [Prefix sums](https://en.algorithmica.org/hpc/algorithms/prefix/) |
| A20 | [Binary search](https://en.algorithmica.org/hpc/data-structures/binary-search/) |
| A21 | [Static search trees](https://en.algorithmica.org/hpc/data-structures/s-tree/) |
| A22 | [SIMD masking](https://en.algorithmica.org/hpc/simd/masking/) |
| A23 | [Memory bandwidth](https://en.algorithmica.org/hpc/cpu-cache/bandwidth/) |
| A24 | [Event-based profiling](https://en.algorithmica.org/hpc/profiling/events/) |
| A26 | [Pointer-based structures](https://en.algorithmica.org/hpc/cpu-cache/pointers/) |
| A27 | [Memory latency](https://en.algorithmica.org/hpc/cpu-cache/latency/) |
| A28 | [Cache associativity](https://en.algorithmica.org/hpc/cpu-cache/associativity/) |
| A29 | [Prefetching](https://en.algorithmica.org/hpc/cpu-cache/prefetching/) |
| A30 | [Moving SIMD data](https://en.algorithmica.org/hpc/simd/moving/) |
| A31 | [Cache sharing](https://en.algorithmica.org/hpc/cpu-cache/sharing/) |

## Measurement and compilers

| ID | Source | Used for |
|---|---|---|
| A25 | [NERSC: Roofline performance model](https://docs.nersc.gov/tools/performance/roofline/) | Compute/bandwidth limits and memory-level-specific intensity |
| T01 | [LLVM: vectorizers](https://llvm.org/docs/Vectorizers.html) | Loop/SLP vectorization, legality, diagnostics and cost considerations |
| T02 | [Linux perf-stat manual](https://man7.org/linux/man-pages/man1/perf-stat.1.html) | Counter collection, repeats, multiplexing and measurement options |
| T03 | [Clang user's manual](https://clang.llvm.org/docs/UsersManual.html) | Optimization diagnostics and floating-point compilation policy |
| T04 | [GCC x86 built-in functions](https://gcc.gnu.org/onlinedocs/gcc/x86-Built-in-Functions.html) | CPU feature checks and baseline-dispatch compilation cautions |

## Rust standard library and SIMD abstractions

| ID | Source | Used for |
|---|---|---|
| R01 | [Rust `Vec`](https://doc.rust-lang.org/std/vec/struct.Vec.html) | Length/capacity, reservation, clearing, allocation and initialized elements |
| R02 | [Rust `MaybeUninit`](https://doc.rust-lang.org/std/mem/union.MaybeUninit.html) | Validity and initialization safety |
| R03 | [Rust `std::arch`](https://doc.rust-lang.org/std/arch/index.html) | Intrinsics, compile/runtime feature selection and safety |
| R04 | [Rust `std::simd`](https://doc.rust-lang.org/std/simd/index.html) | Portable SIMD semantics and nightly-only status at access date |
| R05 | [Rust `black_box`](https://doc.rust-lang.org/std/hint/fn.black_box.html) | Best-effort benchmark optimization barrier and limitations |
| R06 | [Cargo profiles](https://doc.rust-lang.org/cargo/reference/profiles.html) | Optimization, LTO, codegen and panic settings |
| R07 | [`fearless_simd` maintained crate docs](https://docs.rs/fearless_simd/latest/fearless_simd/) | Generic kernels, dispatch and documented integration constraints |
| R08 | [`wide` maintained crate docs](https://docs.rs/wide/latest/wide/) | Fixed-width types and operation semantics |
| R09 | [`pulp` maintained crate docs](https://docs.rs/pulp/latest/pulp/) | Runtime dispatch and generic SIMD interface |

## Allocation and operating systems

| ID | Source | Used for |
|---|---|---|
| M01 | [mimalloc upstream](https://github.com/microsoft/mimalloc) | Allocator design and configurable behavior; not a universal ranking |
| M02 | [jemalloc manual](https://jemalloc.net/jemalloc.3.html) | Allocation statistics, caches, arenas and retention policies |
| M03 | [TCMalloc design](https://google.github.io/tcmalloc/design.html) | Front/middle/back ends, per-CPU/thread caches and memory tradeoffs |
| M04 | [Linux mmap manual](https://man7.org/linux/man-pages/man2/mmap.2.html) | Anonymous mappings, mapping semantics and OS-level memory behavior |
| M05 | [Linux transparent huge pages](https://www.kernel.org/doc/html/latest/admin-guide/mm/transhuge.html) | THP policy and memory-management tradeoffs |

## ISA specifications and numerical implementations

| ID | Source | Used for |
|---|---|---|
| D01 | [Intel Intrinsics Guide](https://www.intel.com/content/www/us/en/docs/intrinsics-guide/index.html) | Intrinsic semantics and instruction feature requirements |
| D02 | [Arm ACLE Advanced SIMD intrinsics](https://arm-software.github.io/acle/neon_intrinsics/advsimd.html) | NEON operations and supported architecture variants |
| N01 | [SLEEF upstream](https://github.com/shibatch/sleef) | Maintained SIMD elementary-function implementation to evaluate |
| N02 | [Arm optimized routines](https://github.com/ARM-software/optimized-routines) | Maintained math/string routines and numeric implementation references |
| N03 | [libdivide](https://libdivide.com/) | Runtime-invariant integer division transformations |

## Evidence boundaries

The bootstrap utility implements a clearly specified engineering decision rule;
it does not claim that Algorithmica prescribes that statistical procedure.
Percentile bootstrap intervals are sensitive to independence, pairing, sample
size, and measurement design. The utility does not certify a performance claim.

The teaching logarithm approximation has a derived real-arithmetic truncation
bound. Its tests are sampled floating-point comparisons, not a proof of a full
compiled floating-point error bound or a replacement for libm. The numerical
reference explains the additional proof needed for threshold-sensitive use.

The package's [validation record](../validation/README.md) is the source for what
was actually executed. Upstream support for an ISA is not evidence that this
package's implementation was executed on that ISA.
