#!/usr/bin/python3
"""
Demo Backend
^^^^^^^^^^^^
Demo backend that prints some
stats about the U-Boot build
"""
import json
import sys


def main():
    """
    Demo backend that prints some
    stats about the U-Boot build
    """
    try:
        log = json.load(open(sys.argv[1]))
    except IndexError:
        sys.stderr.write(
            f"""\
\x1B[1mUsage: {sys.argv[0]} <logfile>\x1B[0m
"""
        )
        sys.exit(1)
    except json.JSONDecodeError:
        sys.stderr.write(
            f"""\
\x1B[31mInvalid JSON!\x1B[0m
\x1B[1mUsage: {sys.argv[0]} <logfile>\x1B[0m
"""
        )
        sys.exit(1)
    except OSError:
        sys.stderr.write(
            f"""\
\x1B[31mopen failed!\x1B[0m
\x1B[1mUsage: {sys.argv[0]} <logfile>\x1B[0m
"""
        )
        sys.exit(1)

    testcases = [
        ("U-Boot git repo setup ", "git_clean_checkout"),
        ("U-Boot build total    ", "@build"),
        ("U-Boot build raw      ", "@compile"),
        ("U-Boot total          ", "uboot_build"),
    ]

    # Get testcase begin and end times
    times = map(
        lambda tc: (
            tc[0],
            [
                e["duration"]
                for e in log
                if e["type"] == ["testcase", "end"] and e["name"] == tc[1]
            ][0],
        ),
        testcases,
    )

    # Print values
    for name, time in times:
        print(f"{name}: {time:.2f}s")


if __name__ == "__main__":
    main()
