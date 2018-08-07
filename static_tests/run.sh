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
    echo "Check if expected errors are deteced ..."
    local output=$(mypy static_tests/path.py)

    run_check "Line 12"; echo "$output" | grep "static_tests/path.py:12:" >/dev/null || check_fail; check_ok
    run_check "Line 18"; echo "$output" | grep "static_tests/path.py:18:" >/dev/null || check_fail; check_ok
    run_check "Line 26"; echo "$output" | grep "static_tests/path.py:26:" >/dev/null || check_fail; check_ok

    run_check "Ensure there were no other errors"; [[ $(echo "$output" | wc -l) = "3" ]] || check_fail; check_ok
}

echo "test_path ..."
test_path
