import sys
import pathlib
import argparse


def new_or_init_cmd(args: argparse.Namespace) -> None:
    base = pathlib.Path.cwd()

    if args.cmd == "new":
        base = base / args.dirname

    if (base / "config").exists():
        print("config/ already exists, can't create TBot config!")
        sys.exit(1)

    (base / "config" / "labs").mkdir(parents=True)
    (base / "config" / "boards").mkdir(parents=True)
    (base / "tc").mkdir(parents=True, exist_ok=True)
