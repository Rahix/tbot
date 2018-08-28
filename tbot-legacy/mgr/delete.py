import sys
import pathlib
import argparse


def del_cmd(args: argparse.Namespace) -> None:
    subdir = None
    if args.del_cmd == "board":
        subdir = "boards"
    elif args.del_cmd == "lab":
        subdir = "labs"
    else:
        print("Unknown subcommand (try -h)!")
        sys.exit(1)

    p = pathlib.Path.cwd() / "config" / subdir / f"{args.name}.py"
    p.unlink()
    print(f"Removed {p}")
