# Systems/prevention extension validation — 2026-09-06

## Scope

Prepared against upstream commit `09dc4b244719aa7f76cf7a26546ca9fe73999c85`.
This is a documentation and skill-routing expansion, not a change to the Rust,
C++, benchmark comparator, or existing verifier implementations. The entry-point
metadata is advanced to 1.1.0; this is not evidence of a published release.

Selected original files and existing test sources were retrieved through the
GitHub connector. Their Git blob SHA-1 identities were checked before editing
or executing. A full local repository clone was unavailable, so the complete
`verify.py` workflow and complete-repository checksum command were **not run**.
Changed-document links were checked against the retrieved upstream file inventory
plus the new files, not by manufacturing placeholder files for missing content.

This x86-64/Linux note is separate from the generated [report.json](report.json),
which records one host per run and may describe a different host. Default-output
verifier runs overwrite that JSON; they do not merge platform coverage. See the
[validation record](README.md) for the committed report's platform and limitations.

## Executed checks

| Check | Result and scope |
|---|---|
| Existing Python comparator tests | PASS: 13 unit tests on Python 3.13.5; unchanged source |
| GCC C++17 release build/tests | PASS: GCC 14.2.0; 3,118,380 correctness checks |
| Clang C++17 release build/tests | PASS: Clang 17.0.0; 3,118,380 correctness checks |
| Clang AddressSanitizer + UndefinedBehaviorSanitizer | PASS: same suite; leak detection requested on Linux |
| Native byte-search implementations | Scalar, dispatch, SSE2 and AVX2 executed; guard-page tests passed |
| x86 assembly presence | Expected compare/mask, shift and integer-add instructions found; not a speed proof |
| Updated Markdown | Frontmatter, local link targets, reference IDs, fenced blocks and whitespace checked |
| Numerical teaching examples | CPU/wall-time, Little's law examples, M/M/1 examples, fan-out and cumulative regression arithmetic checked |
| Patch applicability | Clean apply/reverse checked against byte-verified reconstructed originals |
| Manifest update | Changed/new file digests checked; untouched entries retained from upstream manifest |

The numerical logarithm tests remain sampled comparisons, not exhaustive proof.
Correctness check counts include repeated cases; they are not independent
performance observations. No speedup is claimed for these documentation changes.

## Not executed or not established

Rust compilation/tests: Cargo and rustc unavailable. Native AArch64/NEON: this
environment is x86-64 Linux. Full repository verification/publishing: not run.
Application speed, load/soak/recovery, or cloud capacity: no consuming application
and representative workload supplied. Diagnostic cookbook commands: checked
against documentation, not executed on a user production system. The twelve
[agent scenarios](performance-scenarios.md) are specifications, not completed
model evaluations. Their behavioral outcome remains NOT RUN.

Overall: **available checks passed, with the coverage limits above**. Run the
repository verifier, checksum check, and applicable behavioral/performance checks
in a complete checkout on the required targets before publishing or claiming
application improvement.

## Source and authorship boundary

See [sources.md](../references/sources.md). The complete texts of the two books
were not accessed. Public author/publisher material and primary technical
documentation informed original guides, templates, scenarios, and agent policy.
The dated early-access status of *Fast by Default* must not be represented as
full access to the completed book.
