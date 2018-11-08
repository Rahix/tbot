#!/usr/bin/env bash

output="No output :/"

run_check() {
    echo -n "$1" "... "
}

check_fail() {
    echo "fail."

    echo "----------------------"
    echo "$output"
    exit 1
}

check_ok() {
    echo "ok."
}

test_path() {
    echo "Test static_tests/path.py ..."
    echo "Check if expected errors are deteced ..."
    output=$(mypy --no-incremental static_tests/path.py)

    run_check "Line 13"; echo "$output" | grep "static_tests/path.py:13:" >/dev/null || check_fail; check_ok
    run_check "Line 19"; echo "$output" | grep "static_tests/path.py:19:" >/dev/null || check_fail; check_ok
    run_check "Line 27"; echo "$output" | grep "static_tests/path.py:27:" >/dev/null || check_fail; check_ok
    run_check "Line 30"; echo "$output" | grep "static_tests/path.py:30:" >/dev/null || check_fail; check_ok
    run_check "Line 33"; echo "$output" | grep "static_tests/path.py:33:" >/dev/null || check_fail; check_ok

    run_check "Ensure there were no other errors"; [[ $(echo "$output" | wc -l) = "5" ]] || check_fail; check_ok
}

test_testcase() {
    echo "Test static_tests/testcase.py ..."
    echo "Check if expected errors are deteced ..."
    output=$(mypy --no-incremental static_tests/testcase.py)

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
