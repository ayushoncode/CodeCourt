"""Tests for the Oracle executor."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from oracle.executor import OracleExecutor


def test_correct_solution():
    oracle = OracleExecutor(time_limit=2.0)
    code = "n = int(input()); print(n * 2)"
    result = oracle.run(code, "5", expected_output="10")
    assert result.status == 'pass', f"Expected pass, got {result.status}: {result.stderr}"
    print("✓ test_correct_solution")


def test_wrong_answer():
    oracle = OracleExecutor(time_limit=2.0)
    code = "print(999)"
    result = oracle.run(code, "", expected_output="42")
    assert result.status == 'fail', f"Expected fail, got {result.status}"
    print("✓ test_wrong_answer")


def test_time_limit():
    oracle = OracleExecutor(time_limit=0.5)
    code = "while True: pass"
    result = oracle.run(code, "")
    assert result.status == 'tle', f"Expected tle, got {result.status}"
    print("✓ test_time_limit")


def test_syntax_error():
    oracle = OracleExecutor(time_limit=2.0)
    code = "def broken(:\n    pass"
    result = oracle.run(code, "")
    assert result.status == 'error', f"Expected error, got {result.status}"
    print("✓ test_syntax_error")


def test_multiple_test_cases():
    oracle = OracleExecutor(time_limit=2.0)
    code = "n = int(input()); print(n * n)"
    test_cases = [
        {'input': '2', 'expected': '4'},
        {'input': '3', 'expected': '9'},
        {'input': '5', 'expected': '25'},
    ]
    result = oracle.run_against_tests(code, test_cases)
    assert result['overall_status'] == 'pass', f"Expected pass: {result}"
    assert result['passed'] == 3
    print("✓ test_multiple_test_cases")


def test_partial_pass():
    oracle = OracleExecutor(time_limit=2.0)
    # Correct for even numbers, wrong for odd
    code = "n = int(input()); print(n if n % 2 == 0 else 0)"
    test_cases = [
        {'input': '4', 'expected': '4'},
        {'input': '3', 'expected': '3'},   # Will fail
    ]
    result = oracle.run_against_tests(code, test_cases)
    assert result['passed'] == 1
    assert result['overall_status'] == 'fail'
    print("✓ test_partial_pass")


if __name__ == "__main__":
    print("Running Oracle tests...")
    test_correct_solution()
    test_wrong_answer()
    test_time_limit()
    test_syntax_error()
    test_multiple_test_cases()
    test_partial_pass()
    print("\n✅ All oracle tests passed!")