# Executable examples and tools

These original implementations illustrate contracts, tails, feature dispatch,
allocation reuse, and testing. They are not claims to outperform `memchr`, a
standard library, libm, or an optimized numeric library. Review
[the validation record](../validation/README.md) for actual target coverage.

Run the commands below from the skill directory (`skills/performance-engineering/`
in this repository).

## C++17

[kernels.hpp](cpp/kernels.hpp) contains scalar byte search, SSE2/AVX2 byte search
with dispatch, AArch64 NEON byte search, a modulo-u32 SSE2 prefix sum, four private
histogram tables, first argmin, an overflow-safe pool-fit predicate, and a scalar
positive-u32 teaching logarithm approximation.

```sh
c++ -std=c++17 -O3 -Wall -Wextra -Wpedantic \
    examples/cpp/test_kernels.cpp -o /tmp/performance-kernels
/tmp/performance-kernels
```

The x86 example targets x86-64 with GCC/Clang feature attributes. Do not add a
global `-march=native` or `-mavx2` to a binary intended to run on baseline CPUs.
Optional intrinsics are behind separately targeted functions; the tests call
AVX2 only when the runtime detector permits it. Other compilers/targets use the
supported guarded path or scalar fallback. The NEON example assumes a normal
NEON-enabled AArch64 target. A more general deployment must match its target
policy and feature detection requirements.

Tests cover offsets, vector-boundary sizes, every matching lane, duplicate
matches, zero length, skewed histogram collisions, modular overflow, maximum
argmin values, pool bounds, and sampled logarithm errors. POSIX guard-page tests
put an inaccessible page immediately after the input. Unsupported guard-page
facilities are reported as a skip.

## Dependency-free Rust

[src/lib.rs](rust/src/lib.rs) contains explicit wrapping arithmetic, caller-owned
buffer reuse with fallible reservation, scalar prefix sum, first argmin, four-way
histogram counting, a positive-u32 teaching logarithm, and private SSE2/AVX2/NEON
byte-search backends behind a safe slice API.

```sh
cargo test --offline --manifest-path examples/rust/Cargo.toml --all-targets
cargo test --offline --release --manifest-path examples/rust/Cargo.toml --all-targets
cargo rustc --offline --release --manifest-path examples/rust/Cargo.toml --lib -- --emit=asm
```

The crate does not depend on nightly SIMD or external crates. See
[the Rust guide](../references/rust.md) for integrating `fearless_simd`, `wide`,
`pulp`, or nightly portable SIMD against the consuming project's locked versions.
Do not interpret uncompiled source as tested Rust support. This package's record
explicitly states whether a Rust compiler was available.

## Paired benchmark comparison

The Python utility analyzes **already collected independent paired observations**.
It does not time programs, create a representative workload, correct a biased
experiment, or evaluate memory/quality/p99 gates.

```sh
python3 scripts/compare_benchmarks.py measurements.json \
    --minimum-speedup 0.95 --confidence 0.95 --bootstrap 10000 \
    --min-pairs 10 --bonferroni --output comparison.json
```

Input structure (the numbers below are **synthetic format examples**, not results;
two pairs deliberately fail the default minimum-sample requirement):

```json
{
  "schema_version": 1,
  "metric": "time",
  "unit": "ns/op",
  "environment": {
    "cpu": "record actual CPU",
    "compiler": "record actual compiler and flags",
    "corpus": "record actual identity/hash"
  },
  "cases": [
    {
      "name": "SYNTHETIC-format-example-not-a-measurement",
      "pairs": [
        {"baseline": 100.0, "candidate": 90.0},
        {"baseline": 102.0, "candidate": 92.0}
      ]
    }
  ]
}
```

Use `metric: "time"` for baseline/candidate normalization and `"throughput"`
for candidate/baseline. Keep units and measurement boundaries consistent. Each
case represents one workload/target combination. Do not pair unrelated samples
merely because they occupy corresponding array positions.

The statistic is the geometric mean of paired speedup ratios. The utility
resamples complete pairs via log ratios, constructs a percentile-bootstrap
interval, and optionally adjusts per-case confidence by Bonferroni. A case is
PASS when its interval lower bound reaches the floor, REGRESSION when its upper
bound falls below the floor, and otherwise INCONCLUSIVE. Too few pairs are also
INCONCLUSIVE. A tiny floating-point guard makes exact/near-threshold endpoints
INCONCLUSIVE rather than rounding them into a decision. No across-case aggregate
conceals a required regression.

| Exit | Meaning |
|---|---|
| 0 | All analyzed cases PASS the configured speedup gate |
| 1 | At least one case is a REGRESSION |
| 2 | Invalid input, options, or output-file error |
| 3 | No regression established, but at least one case is INCONCLUSIVE |

A passing 0.95 gate does not prove an improvement. A geometric mean over ratios
is not the ratio of medians or means; select a metric appropriate for the
application. More resamples do not replace independent observations. See
[measurement.md](../references/measurement.md) for the limitations.

## Verify the bundle

```sh
python3 scripts/verify.py
# Also return nonzero for unavailable coverage:
python3 scripts/verify.py --require-all
```

The verifier checks local Markdown links, skill frontmatter, source IDs, Python
unit tests, available GCC/Clang release builds, a sanitizer build, and Rust tests
when Cargo is available. It uses temporary build directories and records skips
in `validation/report.json`. It does not install tools or measure application
speed. `--require-all` will also flag deliberately unperformed application and
exhaustive-numerical validation; inspect the record rather than treating it as a
universal portability certification.
