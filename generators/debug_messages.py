#!/usr/bin/python3
"""
Print all ["msg", ...] log events
"""
import json
import sys


def main():
    """ Main """
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

    for msg in log:
        if msg["type"][0] == "msg":
            print(msg["text"])
            print()


if __name__ == "__main__":
    main()
