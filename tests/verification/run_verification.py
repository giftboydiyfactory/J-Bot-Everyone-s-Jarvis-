#!/usr/bin/env python3
"""J-Bot Feedback-Based Verification System.

Runs test cases derived from real user feedback:
- Positive cases: outputs that received user approval
- Negative cases: outputs that must never recur

Usage:
    python run_verification.py [--report]
"""
import json
import os
import sys
from pathlib import Path

TESTS_FILE = Path(__file__).parent / "feedback_tests.json"
RESULTS_FILE = Path(__file__).parent / "last_results.json"


def load_tests():
    with open(TESTS_FILE, encoding="utf-8") as f:
        return json.load(f)


def check_positive(case: dict, response: str) -> dict:
    """Check a positive test case against a response."""
    passed = True
    failures = []

    for expected in case.get("expected_contains", []):
        if expected.lower() not in response.lower():
            passed = False
            failures.append(f"Missing: '{expected}'")

    for forbidden in case.get("expected_not_contains", []):
        if forbidden.lower() in response.lower():
            passed = False
            failures.append(f"Contains forbidden: '{forbidden}'")

    return {"id": case["id"], "passed": passed, "failures": failures}


def check_negative(case: dict, response: str) -> dict:
    """Check a negative test case — response must NOT contain forbidden content."""
    passed = True
    failures = []

    for forbidden in case.get("must_not_contain", []):
        if forbidden.lower() in response.lower():
            passed = False
            failures.append(f"Contains forbidden: '{forbidden}'")

    return {"id": case["id"], "passed": passed, "failures": failures}


def run_all(responses: dict = None) -> dict:
    """Run all test cases. If responses not provided, just validate structure."""
    tests = load_tests()
    results = {
        "positive": [],
        "negative": [],
        "summary": {"total": 0, "passed": 0, "failed": 0}
    }

    total = len(tests["positive_cases"]) + len(tests["negative_cases"])
    passed = 0

    if responses:
        for case in tests["positive_cases"]:
            resp = responses.get(case["id"], "")
            r = check_positive(case, resp)
            results["positive"].append(r)
            if r["passed"]:
                passed += 1

        for case in tests["negative_cases"]:
            resp = responses.get(case["id"], "")
            r = check_negative(case, resp)
            results["negative"].append(r)
            if r["passed"]:
                passed += 1

    results["summary"] = {
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "pass_rate": f"{passed/total*100:.0f}%" if total > 0 else "N/A"
    }

    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    return results


if __name__ == "__main__":
    tests = load_tests()
    print(f"Verification System v{tests['version']}")
    print(f"Positive cases: {len(tests['positive_cases'])}")
    print(f"Negative cases: {len(tests['negative_cases'])}")
    print(f"Total: {len(tests['positive_cases']) + len(tests['negative_cases'])}")

    if "--report" in sys.argv:
        results = run_all()
        print(json.dumps(results["summary"], indent=2))
