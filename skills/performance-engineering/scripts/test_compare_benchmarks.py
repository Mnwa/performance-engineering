#!/usr/bin/env python3
import copy
import math
import unittest
from compare_benchmarks import analyze, no_duplicate_keys


def fixture(candidate=80, n=12, metric="time"):
    return {"schema_version": 1, "metric": metric, "unit": "synthetic units",
            "cases": [{"name": "SYNTHETIC-NOT-A-MEASUREMENT",
                       "pairs": [{"baseline": 100, "candidate": candidate} for _ in range(n)]}]}


def run(data, **kwargs):
    return analyze(data, bootstrap=1000, **kwargs)


class TestPairedAnalysis(unittest.TestCase):
    def test_pass(self):
        r = run(fixture())
        self.assertEqual(r["overall"], "PASS")
        self.assertAlmostEqual(r["cases"][0]["speedup"], 1.25)

    def test_exact_gate_boundary_is_conservative(self):
        # log(95)-log(100) can round below log(0.95). Do not declare a regression.
        self.assertEqual(run(fixture(95, metric="throughput"))["overall"], "INCONCLUSIVE")
        self.assertEqual(run(fixture(100), minimum_speedup=1.0)["overall"], "INCONCLUSIVE")

    def test_regression(self):
        self.assertEqual(run(fixture(120))["overall"], "REGRESSION")

    def test_throughput_direction(self):
        self.assertEqual(run(fixture(120, metric="throughput"))["overall"], "PASS")
        self.assertEqual(run(fixture(80, metric="throughput"))["overall"], "REGRESSION")

    def test_insufficient_not_pass(self):
        r = run(fixture(1, n=2))
        self.assertEqual(r["overall"], "INCONCLUSIVE")
        self.assertIsNone(r["cases"][0]["interval"])

    def test_uncertain(self):
        data = fixture()
        data["cases"][0]["pairs"] = [{"baseline": 100, "candidate": x} for x in [70, 150] * 6]
        self.assertEqual(run(data)["overall"], "INCONCLUSIVE")

    def test_no_hidden_case_regression(self):
        data = fixture(50)
        bad = fixture(200)["cases"][0]
        bad["name"] = "second-required-case"
        data["cases"].append(bad)
        self.assertEqual(run(data)["overall"], "REGRESSION")

    def test_bonferroni(self):
        data = fixture()
        second = copy.deepcopy(data["cases"][0]); second["name"] = "second"
        data["cases"].append(second)
        self.assertAlmostEqual(run(data, bonferroni=True)["per_case_confidence"], 0.975)

    def test_invalid_values(self):
        for x in [0, -1, math.nan, math.inf, True, "10", None]:
            data = fixture(); data["cases"][0]["pairs"][0]["candidate"] = x
            with self.subTest(x=x), self.assertRaises(ValueError): run(data)

    def test_invalid_structure(self):
        for data in [{}, {"schema_version": True}, {**fixture(), "cases": []},
                     {**fixture(), "metric": "unknown"}, {**fixture(), "unit": ""}]:
            with self.assertRaises(ValueError): run(data)
        data = fixture(); data["cases"].append(copy.deepcopy(data["cases"][0]))
        with self.assertRaises(ValueError): run(data)
        data = fixture(); del data["cases"][0]["pairs"][0]["baseline"]
        with self.assertRaises(ValueError): run(data)

    def test_duplicate_json_keys(self):
        with self.assertRaises(ValueError): no_duplicate_keys([("x", 1), ("x", 2)])

    def test_deterministic_seed(self):
        data = fixture()
        data["cases"][0]["pairs"] = [{"baseline": 100 + i, "candidate": 80 - i} for i in range(12)]
        self.assertEqual(run(data), run(data))

    def test_invalid_policy(self):
        for kwargs in [{"minimum_speedup": 0}, {"confidence": 1}, {"min_pairs": 1}]:
            with self.assertRaises(ValueError): run(fixture(), **kwargs)
        with self.assertRaises(ValueError): analyze(fixture(), bootstrap=10)


if __name__ == "__main__":
    unittest.main(verbosity=2)
