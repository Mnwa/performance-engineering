# Sources and provenance

Original low-level sources checked **2026-09-05**. New systems, prevention, and
supporting operational sources checked **2026-09-06**. Source IDs used throughout
the skill refer to the entries below. Exact instruction behavior, crate APIs, and compiler options must be
verified against the target and locked version used by a consuming project.

This is an original operational synthesis, not a reproduction of the cited
books or author materials. The examples, pool-fit predicate proof, histogram-score error-budget
application, suggested regression policy, report template, and verification
scripts were written for this package. Mathematical derivations are identified
as such; historical timings and speedup claims from sources are not transferred
to this package. Refer to upstream sources for their own authorship and licenses.

Source IDs establish provenance, not self-contained verification from this
package. Entries below include public primary sources that readers can inspect,
but source texts are not bundled and an ID alone does not prove that a claim
matches its source. The [verifier](../scripts/verify.py) checks local links and
whether reference IDs are defined; it does not validate external source contents,
availability, or freshness. The workflows and policies remain the original
synthesis described above.

## Time-sensitive claims to re-verify

Before each release, and after a relevant toolchain, dependency, platform, or
publisher-status change, review this checklist against the primary sources.
This is a manual maintenance surface, not an automated freshness guarantee.
Add new dated or version-sensitive claims here and update affected text and
check dates only after verification; do not advance dates merely to clear a review.

| Claim or guidance | Where to recheck | Recorded check and refresh trigger |
|---|---|---|
| `std::simd` nightly-only / `portable_simd` status | [Rust SIMD selection](rust.md#choose-a-simd-layer-deliberately); R04 | Official documentation rechecked 2026-09-07; recheck before changing the stable-toolchain requirement. This is a documentation check, not a compilation result. |
| *Fast by Default* early-access chapter count and estimated publication | [Publisher-status snapshot](#fast-by-default-and-prevention-first-engineering), [prevention guide](fast-by-default.md); F01, F02 | Retained 2026-09-06 snapshot; recheck before describing current availability or attributing new material. Full book access must not be inferred. |
| SIMD crate APIs, target support, and compiler integration | [Rust guide](rust.md), [SIMD guide](simd.md); R03, R06, R07, R08, R09, T01, T03, T04, D01, D02 | Original source review 2026-09-05; verify the consuming project's locked versions, features, target, and generated code when any of them changes. Live `/latest/` docs are not a version pin. |
| Allocator behavior, OS interfaces, and diagnostic command options | [Allocation guide](allocations.md), [OS diagnostics](operating-system-diagnostics.md); M01, M02, M03, M04, M05, O01, O02, O03, O05, O09, O10, O11, T02, T05 | Original source reviews 2026-09-05/2026-09-06; recheck against the deployed OS and installed tool versions before applying target-specific guidance. |

Dates in validation notes and `report.json` describe historical executions, not
current coverage for every host or release. Preserve those dates and record fresh
runs separately rather than relabeling old evidence.

## Conceptual foundation: Algorithmica

Author: Sergey Slotin. Work: *Algorithms for Modern Hardware*.

A25 is listed under [Measurement and compilers](#measurement-and-compilers):
it identifies the NERSC Roofline source, not an Algorithmica chapter. Source IDs
are stable provenance keys, not a reading sequence.

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

## Systems Performance and public methodology

Brendan Gregg, *Systems Performance: Enterprise and the Cloud*, second edition
(Addison-Wesley, 2020). The book's author page and public methodology articles
were consulted; the full book text was not accessed. The new guides translate
verified methods into original agent workflows, not chapter summaries or page
quotations. Historical tool examples still require target-version verification.

| ID | Primary source | Used for |
|---|---|---|
| S01 | [Author's second-edition book page](https://www.brendangregg.com/systems-performance-2nd-edition-book.html) | Book identity, scope, resource and cloud coverage |
| S02 | [Performance analysis methodology](https://www.brendangregg.com/methodology.html) | Problem statement, workload characterization, method selection |
| S03 | [The USE Method](https://www.brendangregg.com/usemethod.html) | Utilization, saturation, errors and resource inventory |
| S04 | [Thread State Analysis](https://www.brendangregg.com/tsamethod.html) | Execution, runnable delay, waiting and idle distinctions |
| S05 | [Off-CPU Analysis](https://www.brendangregg.com/offcpuanalysis.html) | Complementing CPU profiles with wait analysis |
| S06 | [Active Benchmarking](https://www.brendangregg.com/activebenchmarking.html) | Observing what a benchmark and generator actually exercise |
| S07 | [Flame Graphs](https://www.brendangregg.com/flamegraphs.html) | Aggregated stacks, sample meaning, and non-chronological layout |

## Fast by Default and prevention-first engineering

Den Odell, *Fast by Default: Practical Performance Engineering* (Manning, MEAP).
On **2026-09-06**, the publisher listed 8 of 20 chapters available, a July 2026
update, and an estimated Spring 2027 publication. This is not a claim that the
completed book was available or read. The full book text was not accessed.

The public model and publisher description support the prevention-first themes;
the detailed budgets, CI policy, load plans, worked examples, and evaluation
rubrics are this skill's original synthesis. The publisher names System Paths,
but unavailable taxonomy, chapter details, quotations, and page numbers must
not be invented. Recheck the publisher before relying on this dated status.

| ID | Primary source | Used for |
|---|---|---|
| F01 | [Manning: Fast by Default](https://www.manning.com/books/fast-by-default) | Book identity, early-access status, stated scope and evidence boundary |
| F02 | [Author's public Fast by Default model](https://fastbydefault.com/) | Principles, cycle, practical steps, budgets and ongoing ownership |
| F03 | [Author's companion code repository](https://github.com/denodell/fast-by-default) | Companion resource provenance; no code copied and no full-chapter access implied |

## Supporting systems and service documentation

| ID | Primary source | Used for |
|---|---|---|
| O01 | [Linux cgroup v2](https://docs.kernel.org/admin-guide/cgroup-v2.html) | Hierarchical CPU/memory controls and accounting |
| O02 | [Linux pressure stall information](https://docs.kernel.org/accounting/psi.html) | Pressure measurements and scope |
| O03 | [Linux proc filesystem](https://docs.kernel.org/filesystems/proc.html) | Process/system memory accounting and observation boundaries |
| O04 | [Prometheus: histograms and summaries](https://prometheus.io/docs/practices/histograms/) | Quantile aggregation and histogram accuracy limits |
| O05 | [Sysstat project documentation](https://sysstat.github.io/) | Monitoring tool scope and upstream documentation |
| O06 | [Google SRE: Monitoring Distributed Systems](https://sre.google/sre-book/monitoring-distributed-systems/) | User-facing latency, traffic, errors, saturation |
| O07 | [Grafana k6: open and closed models](https://grafana.com/docs/k6/latest/using-k6/scenarios/concepts/open-vs-closed/) | Arrival-model feedback and coordinated omission |
| O08 | [Google SRE: Handling Overload](https://sre.google/sre-book/handling-overload/) | Useful capacity, queues, admission and overload behavior |
| O09 | [Sysstat iostat manual](https://man7.org/linux/man-pages/man1/iostat.1.html) | Command options, I/O metrics, and parallel-device utilization caveat |
| O10 | [Sysstat pidstat manual](https://man7.org/linux/man-pages/man1/pidstat.1.html) | Process-scoped CPU, memory, I/O and scheduling reports |
| O11 | [Sysstat mpstat manual](https://man7.org/linux/man-pages/man1/mpstat.1.html) | Per-CPU reports and bounded interval/count syntax |
| T05 | [Linux perf-record manual](https://man7.org/linux/man-pages/man1/perf-record.1.html) | Sampling frequency, call graphs and attach scope |
| Q01 | [MIT, Urban Operations Research, section 4.4](https://web.mit.edu/urban_or_book/www/book/chapter4/4.4.html) | Little's law, matching boundaries, admitted flow and long-run averages |
| Q02 | [MIT, Urban Operations Research, section 4.6.1](https://web.mit.edu/urban_or_book/www/book/chapter4/4.6.1.html) | M/M/1 assumptions and mean residence-time model |

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

The new numerical scenarios are hypothetical derivations, not measured case
studies. The `0.95` gate, evidence ledger, suggested CI tiers, safety policies,
and evaluation rubrics are package recommendations, not numerical prescriptions
attributed to Gregg or Odell. Agent evaluation scenarios remain specifications
until responses are actually run and assessed.
