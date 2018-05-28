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
    except:  # pylint: disable=broad-except
        print(f"\x1B[1mUsage: {sys.argv[0]} <logfile>\x1B[0m\n")
        raise

    for msg in log:
        if msg["type"][0] == "msg":
            print(msg["text"])
            print()


if __name__ == "__main__":
    main()
