#!/usr/bin/python3
"""
Demo backend that prints some
stats about the U-Boot build
"""
import json
import sys

def main():
    """ Main """
    try:
        log = json.load(open(sys.argv[1]))
    except: #pylint: disable=broad-except
        print(f"\x1B[1mUsage: {sys.argv[0]} <logfile>\x1B[0m\n")
        raise


    testcases = [
        ("U-Boot git repo setup ", "git_clean_checkout"),
        ("U-Boot build total    ", "@build"),
        ("U-Boot build raw      ", "@compile"),
        ("U-Boot total          ", "uboot_build"),
        ]

    # Get testcase begin and end times
    times = map(lambda tc: (tc[0], [e['duration']
                                    for e in log
                                    if e['type'] == ['testcase', 'end'] and e['name'] == tc[1]][0]),
                testcases)

    # Print values
    for name, time in times:
        print(f"{name}: {time:.2f}s")

if __name__ == "__main__":
    main()
