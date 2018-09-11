#!/usr/bin/env bash

run_check() {
    echo -n "$1" "... "
}

check_fail() {
    echo "fail."
    exit 1
}

check_ok() {
    echo "ok."
}

test_path() {
    echo "Test static_tests/path.py ..."
    echo "Check if expected errors are deteced ..."
    local output=$(mypy static_tests/path.py)

    run_check "Line 12"; echo "$output" | grep "static_tests/path.py:12:" >/dev/null || check_fail; check_ok
    run_check "Line 18"; echo "$output" | grep "static_tests/path.py:18:" >/dev/null || check_fail; check_ok
    run_check "Line 26"; echo "$output" | grep "static_tests/path.py:26:" >/dev/null || check_fail; check_ok

    run_check "Ensure there were no other errors"; [[ $(echo "$output" | wc -l) = "3" ]] || check_fail; check_ok
}

test_testcase() {
    echo "Test static_tests/testcase.py ..."
    echo "Check if expected errors are deteced ..."
    local output=$(mypy static_tests/testcase.py)

    run_check "Line 23"; echo "$output" | grep "static_tests/testcase.py:23:" >/dev/null || check_fail; check_ok
    run_check "Line 24"; echo "$output" | grep "static_tests/testcase.py:24:" >/dev/null || check_fail; check_ok

    run_check "Line 31"; echo "$output" | grep "static_tests/testcase.py:31:" >/dev/null || check_fail; check_ok
    run_check "Line 32"; echo "$output" | grep "static_tests/testcase.py:32:" >/dev/null || check_fail; check_ok
    run_check "Line 33"; echo "$output" | grep "static_tests/testcase.py:33:" >/dev/null || check_fail; check_ok
    run_check "Line 34"; echo "$output" | grep "static_tests/testcase.py:34:" >/dev/null || check_fail; check_ok

    run_check "Ensure there were no other errors"; [[ $(echo "$output" | wc -l) = "6" ]] || check_fail; check_ok
}

echo "test_path ..."
test_path
test_testcase
