#!/usr/bin/env python3
"""Validate the bundle and run available native checks, recording unavailable coverage.

Does not install tools, alter host settings, or claim performance results.
Exit 0: executed checks passed (inspect skips); 1: failure; 2: --require-all had skips.
"""
from __future__ import annotations
import argparse
import datetime
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def package_errors() -> list[str]:
    errors: list[str] = []
    entry = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    if not entry.startswith("---\n") or "\n---\n" not in entry[4:]:
        errors.append("SKILL.md: missing YAML frontmatter")
    if "name: performance-engineering\n" not in entry or "description: " not in entry:
        errors.append("SKILL.md: missing name/description")
    for path in ROOT.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            relative = target.split("#", 1)[0]
            if not (path.parent / relative).exists():
                errors.append(f"{path.relative_to(ROOT)}: broken local link {target}")
    sources = (ROOT / "references/sources.md").read_text(encoding="utf-8")
    known = set(re.findall(r"^\| ([A-Z]\d{2}) \|", sources, flags=re.M))
    for path in (ROOT / "references").glob("*.md"):
        if path.name == "sources.md":
            continue
        for source in set(re.findall(r"\b[A-Z]\d{2}\b", path.read_text(encoding="utf-8"))):
            if source not in known:
                errors.append(f"{path.name}: undefined source {source}")
    return errors


def execute(name: str, command: list[str], results: list[dict[str, Any]],
            *, env: dict[str, str] | None = None, timeout: int = 120) -> bool:
    try:
        completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True,
                                   timeout=timeout, env=env)
        passed = completed.returncode == 0
        results.append({"name": name, "status": "PASS" if passed else "FAIL",
                        "command": command, "returncode": completed.returncode,
                        "stdout": completed.stdout, "stderr": completed.stderr})
    except (OSError, subprocess.TimeoutExpired) as exc:
        passed = False
        results.append({"name": name, "status": "FAIL", "command": command, "error": str(exc)})
    print(f"{name}: {'PASS' if passed else 'FAIL'}", flush=True)
    return passed


def skip(name: str, reason: str, results: list[dict[str, Any]]) -> None:
    results.append({"name": name, "status": "SKIP", "reason": reason})
    print(f"{name}: SKIP ({reason})", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "validation/report.json")
    parser.add_argument("--require-all", action="store_true")
    args = parser.parse_args()
    results: list[dict[str, Any]] = []
    errors = package_errors()
    results.append({"name": "package_links_frontmatter_sources", "status": "FAIL" if errors else "PASS", "errors": errors})
    print("package_links_frontmatter_sources:", "FAIL" if errors else "PASS", flush=True)
    execute("python_unit_tests", [sys.executable, "-m", "unittest", "discover", "-s", "scripts", "-p", "test_*.py", "-v"], results)
    source = str(ROOT / "examples/cpp/test_kernels.cpp")
    with tempfile.TemporaryDirectory(prefix="performance-engineering-") as temporary:
        build = Path(temporary)
        compilers = [name for name in ("g++", "clang++") if shutil.which(name)]
        for compiler in ("g++", "clang++"):
            location = shutil.which(compiler)
            if not location:
                skip(f"cpp_{compiler}", "compiler unavailable", results)
                continue
            execute(f"{compiler}_version", [location, "--version"], results)
            output = str(build / ("test-" + compiler.replace("+", "p")))
            command = [location, "-std=c++17", "-O3", "-Wall", "-Wextra", "-Wpedantic", source, "-o", output]
            if execute(f"cpp_{compiler}_release_build", command, results):
                execute(f"cpp_{compiler}_release_tests", [output], results)
        if compilers and platform.machine().lower() in ("x86_64", "amd64"):
            compiler = shutil.which("g++") or shutil.which("clang++")
            assembly = build / "kernels.s"
            command = [str(compiler), "-std=c++17", "-O3", "-S", "-masm=intel", source, "-o", str(assembly)]
            if execute("cpp_x86_assembly_build", command, results):
                text = assembly.read_text(encoding="utf-8")
                instructions = ["pcmpeqb", "pmovmskb", "vpcmpeqb", "vpmovmskb", "pslldq", "paddd"]
                counts = {op: len(re.findall(r"\b" + op + r"\b", text)) for op in instructions}
                ok = all(counts.values())
                results.append({"name": "cpp_x86_expected_instructions", "status": "PASS" if ok else "FAIL",
                                "instruction_counts": counts,
                                "limitation": "Presence is inspected, not performance or dispatch safety certification."})
                print("cpp_x86_expected_instructions:", "PASS" if ok else "FAIL", flush=True)
        if compilers:
            # Prefer Clang sanitizer runtime where available; no benchmark uses instrumentation.
            compiler = shutil.which("clang++") or shutil.which("g++")
            output = str(build / "test-sanitized")
            command = [str(compiler), "-std=c++17", "-O1", "-g", "-fsanitize=address,undefined",
                       "-fno-omit-frame-pointer", source, "-o", output]
            if execute("cpp_sanitizer_build", command, results):
                # LeakSanitizer exists only on some platforms; requesting it elsewhere aborts the run.
                leaks = "1" if platform.system() == "Linux" else "0"
                env = dict(os.environ, ASAN_OPTIONS=f"detect_leaks={leaks}:halt_on_error=1",
                           UBSAN_OPTIONS="halt_on_error=1:print_stacktrace=1")
                execute("cpp_asan_ubsan_tests", [output], results, env=env)
                if leaks == "0":
                    skip("cpp_leak_detection", f"LeakSanitizer unavailable on {platform.system()}; leaks are not checked here", results)
        else:
            skip("cpp_sanitizers", "no C++ compiler available", results)
        cargo = shutil.which("cargo")
        if cargo:
            execute("rustc_version", [shutil.which("rustc") or "rustc", "--version"], results)
            env = dict(os.environ, CARGO_TARGET_DIR=str(build / "rust-target"))
            for mode in ([], ["--release"]):
                suffix = "release" if mode else "debug"
                execute(f"rust_{suffix}_tests", [cargo, "test", "--offline", "--manifest-path",
                        str(ROOT / "examples/rust/Cargo.toml"), "--all-targets", *mode], results, env=env)
        else:
            skip("rust_compilation_and_tests", "cargo/rustc unavailable; Rust source is not compiled or executed", results)
    machine = platform.machine().lower()
    if machine not in ("aarch64", "arm64"):
        skip("native_aarch64_neon", "not running on AArch64; NEON code is not compiled or executed here", results)
    if machine not in ("x86_64", "amd64"):
        skip("native_x86_64_sse2_avx2", "not running on x86-64; inspect runtime CPU support for optional AVX2", results)
    skip("application_performance_benchmarks", "no user application/corpus; correctness tests are not speed measurements", results)
    skip("exhaustive_u32_numeric_proof", "logarithm tests sample inputs; full compiled floating-point bound is not certified", results)
    failed = any(result["status"] == "FAIL" for result in results)
    has_skips = any(result["status"] == "SKIP" for result in results)
    overall = "FAIL" if failed else "PASS_WITH_SKIPS" if has_skips else "PASS"
    report = {"generated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "platform": platform.platform(), "machine": machine,
              "python": sys.version, "overall": overall,
              "not_a_performance_benchmark": True, "checks": results}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"Overall: {overall}\nReport: {args.output}", flush=True)
    return 1 if failed else 2 if args.require_all and has_skips else 0


if __name__ == "__main__":
    raise SystemExit(main())
