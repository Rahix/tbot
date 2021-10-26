#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
import argparse
import importlib
import os
import sys
import typing
from typing import Optional, Sequence

if typing.TYPE_CHECKING:
    import tbot


def load_config(config: str, ctx: "tbot.Context") -> None:
    args: Sequence[Optional[str]]

    config_name, *args = config.split(":")
    config_module = importlib.import_module(config_name)

    # Replace empty args with `None`
    args = [(arg if arg != "" else None) for arg in args]

    if not hasattr(config_module, "register_machines"):
        raise AttributeError(f"{config_name} is missing `register_machines()`")

    getattr(config_module, "register_machines")(ctx, *args)


def run_testcase(testcase: str) -> None:
    module_name, function_name = testcase.rsplit(".", 1)
    module = importlib.import_module(module_name)

    if not hasattr(module, function_name):
        raise AttributeError(f"`{module_name}` does not contain `{function_name}()`")

    getattr(module, function_name)()


def get_version() -> str:
    try:
        from importlib import metadata

        try:
            return metadata.version("tbot")  # type: ignore
        except metadata.PackageNotFoundError:  # type: ignore
            pass
    except ImportError:
        pass

    try:
        from tbot import _version

        return _version.version
    except ImportError:
        pass

    return "unknown"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tbot",
        description="Test and development automation tool, tailored for embedded"
        + " (experimental new CLI)",
        fromfile_prefix_chars="@",
    )

    parser.add_argument(
        "-C",
        metavar="WORKDIR",
        dest="workdir",
        help="use WORKDIR as working directory instead of the current directory.",
    )

    parser.add_argument("-b", "--board", help="alias for `-c`")
    parser.add_argument("-l", "--lab", help="alias for `-c`")
    parser.add_argument("-c", "--config", nargs=1, action="extend", default=[])

    parser.add_argument(
        "-f",
        metavar="FLAG",
        dest="flags",
        action="append",
        default=[],
        help="set a user defined flag to change testcase behaviour",
    )

    parser.add_argument(
        "-v", dest="verbosity", action="count", default=0, help="increase the verbosity"
    )

    parser.add_argument(
        "-q", dest="quiet", action="count", default=0, help="decrease the verbosity"
    )

    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {get_version()}"
    )

    parser.add_argument("testcase", nargs="*", help="testcase that should be run.")

    return parser


def main(argv: Optional[Sequence[str]] = None) -> None:
    parser = build_parser()

    args = parser.parse_args(argv)

    if args.workdir:
        os.chdir(args.workdir)

    # Make sure the directory we're running from is available
    sys.path.insert(1, os.getcwd())

    import tbot
    import tbot.log
    import tbot.log_event

    for flag in args.flags:
        tbot.flags.add(flag)

    tbot.log.VERBOSITY = tbot.log.Verbosity(
        tbot.log.Verbosity.STDOUT + args.verbosity - args.quiet
    )

    tbot.log_event.tbot_start()

    # Use the tbot.ctx as our default context
    ctx = tbot.ctx

    if args.lab is not None:
        load_config(args.lab, ctx)
    if args.board is not None:
        load_config(args.board, ctx)
    for config in args.config:
        load_config(config, ctx)

    try:
        with ctx:
            for testcase in args.testcase:
                run_testcase(testcase)
    except Exception as e:
        import traceback

        trace = traceback.format_exc()
        tbot.log_event.exception(e.__class__.__name__, trace)
        tbot.log_event.tbot_end(False)
        sys.exit(1)
    except KeyboardInterrupt:
        tbot.log_event.exception("KeyboardInterrupt", "Test run manually aborted.")
        tbot.log_event.tbot_end(False)
        sys.exit(130)
    except SystemExit as e:
        tbot.log.message("SystemExit triggered.")
        tbot.log_event.tbot_end(e.code in (None, 0))
        raise e
    else:
        tbot.log_event.tbot_end(True)


if __name__ == "__main__":
    main(sys.argv)
