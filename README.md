# Performance engineering — reusable agent skill

[![skills.sh](https://skills.sh/b/Mnwa/performance-engineering)](https://skills.sh/Mnwa/performance-engineering)

A measurement-first skill for designing and optimizing CPU software. Its
foundation is Algorithmica's *Algorithms for Modern Hardware*, expanded with
allocation lifecycle analysis, computation and numerical contracts, SIMD
correctness recipes, Rust integration, and executable validation tools.

## Install

Install it with the [skills CLI](https://skills.sh/docs/cli):

```bash
npx skills add Mnwa/performance-engineering
```

For a manual installation, copy the complete `performance-engineering` folder
into the skill directory recognized by your agent runtime, keeping the directory
name unchanged because it matches the `name` in `SKILL.md`.

## Use

The entry point is [SKILL.md](SKILL.md). This package does not install itself or
change an agent's configuration. A runtime without automatic skill discovery can
read `SKILL.md` explicitly and follow its relative reference links.

Example task:

> Use the performance-engineering skill to optimize this kernel. Preserve exact
> output and first-match semantics. Target x86-64 SSE2/AVX2 and AArch64 NEON.
> Profile before changing it; prioritize allocation, repeated work, and layout.
> Test SIMD tails and fallbacks, measure retained memory, and report per-case
> speedup against a configurable 0.95 no-regression floor. Do not invent results.

For new software, replace “optimize this kernel” with the required behavior,
workload, resource budget, and target platform. The agent should create a simple
correct baseline before specializing it.

## Contents

- `SKILL.md`: compact entry point and required optimization workflow.
- `references/`: focused allocation, memory, computation, SIMD, algorithm,
  measurement, parallelism, Rust, and source guides.
- `examples/`: original dependency-free Rust and C++ teaching kernels and tests.
- `scripts/`: package verification and paired benchmark analysis.
- `templates/`: reproducible optimization report.
- `validation/`: what was actually tested when this package was assembled.
- `agents/`, `assets/`: packaging metadata and icon for skill directories.
- `MANIFEST.sha256`: SHA-256 of every packaged file except itself and
  `validation/report.json`, which `scripts/verify.py` regenerates. Check it with
  `shasum -a 256 -c MANIFEST.sha256`.

Read [examples/README.md](examples/README.md) for build commands and the benchmark
input format. Run `python3 scripts/verify.py` from this folder to check local
coverage; unavailable compilers and targets are reported, not treated as passes.

The examples are not replacements for a tuned standard library, a complete
allocator, or a validated vector-math library. No speedup is claimed without
application measurements. The suggested 0.95 speedup gate is configurable and
does not replace memory, quality, correctness, or latency requirements.

Sources were checked on **2026-09-05**. Exact library APIs and toolchain status
must be rechecked against the consuming project's lockfile and build policy.
See [references/sources.md](references/sources.md) for provenance.
