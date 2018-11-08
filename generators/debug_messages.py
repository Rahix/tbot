#!/usr/bin/env python3
"""Print all ["msg", ...] log events."""
import sys
import logparser


def main() -> None:
    """Main."""
    try:
        events = logparser.logfile(sys.argv[1])
    except IndexError:
        sys.stderr.write(
            f"""\
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

    for ev in events:
        if ev.type[0] == "msg":
            print(ev.data["text"])
            print()


if __name__ == "__main__":
    main()
