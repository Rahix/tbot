#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
import argparse
import importlib
import itertools
import os
import pathlib
import string
import sys
import typing
from typing import Iterable, List, Optional, Sequence

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


def complete_module(cur: str) -> Iterable[str]:
    # There are already arguments being passed now - nothing to complete anymore.
    if ":" in cur:
        return ()

    components = cur.rsplit(".", 1)
    if len(components) == 2:
        modpath = components[0] + "."
        path = pathlib.Path(components[0].replace(".", "/"))
        frag = components[1]
    else:
        modpath = ""
        path = pathlib.Path(".")
        frag = components[0]

    # If the module directory is missing, we won't find anything so return
    # early.
    if not path.is_dir():
        return ()

    # If the fragment already marks an existing submodule, we can complete
    # inside it instead.  Append it to the path, as if a trailing `.` was
    # passed.
    if frag != "" and (path / frag).is_dir():
        modpath += frag + "."
        path = path / frag
        frag = ""

    # Collect all subdirectories and python script files as potential module
    # names.
    candidates = []
    for child in path.iterdir():
        if child.name.startswith(frag) and not child.name.startswith("__"):
            if child.is_dir():
                candidates.append(child.name)
            elif child.is_file() and child.suffix == ".py":
                candidates.append(child.stem)

    return (modpath + c for c in sorted(candidates))


def complete_testcase(cur: str) -> Iterable[str]:
    components = cur.rsplit(".", 1)
    if len(components) == 1:
        return complete_module(cur)

    modpath = components[0]
    path = pathlib.Path(components[0].replace(".", "/"))
    frag = components[1]

    if frag != "" and (path / frag).with_suffix(".py").is_file():
        path = path / frag
        modpath += "." + frag
        frag = ""

    if not path.with_suffix(".py").is_file() and not (path / "__init__.py").is_file():
        return complete_module(cur)

    module = importlib.import_module(modpath)
    callables = (f for f in dir(module) if callable(getattr(module, f, None)))
    matching = (modpath + "." + f for f in callables if f.startswith(frag))

    if path.is_dir():
        matching_mods = complete_module(cur)
        return itertools.chain(matching_mods, matching)
    else:
        return matching


def get_version() -> str:
    try:
        from importlib import metadata  # type: ignore

        try:
            return metadata.version("tbot")  # type: ignore
        except metadata.PackageNotFoundError:  # type: ignore
            pass
    except ImportError:
        pass

    try:
        from tbot import _version  # type: ignore

        return _version.version  # type: ignore
    except ImportError:
        pass

    return "unknown"


def build_parser() -> argparse.ArgumentParser:
    parser = TbotArgumentParser(
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
    parser.add_argument("-c", "--config", action="append", default=[])

    parser.add_argument(
        "-f",
        metavar="FLAG",
        dest="flags",
        action="append",
        default=[],
        help="set a user defined flag to change testcase behaviour",
    )

    parser.add_argument(
        "-k",
        "--keep-alive",
        dest="keep_alive",
        action="store_true",
        default=False,
        help="keep machines alive for later tests to reacquire them",
    )

    parser.add_argument(
        "--json-log-stream", metavar="LOGFILE", help="write a log to the specified file"
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


class TbotArgumentParser(argparse.ArgumentParser):
    def convert_arg_line_to_args(self, arg_line: str) -> List[str]:
        """
        Make it possible to use shell variables also in argumentsfiles.
        """
        try:
            arg_line_expanded = string.Template(arg_line).substitute(os.environ)
        except KeyError as e:
            raise tbot.error.TbotException(
                f"Could not find environment variable: {e.args[0]!r}"
            ) from None

        return [arg_line_expanded]


def main(argv: Optional[Sequence[str]] = None) -> None:
    parser = build_parser()

    parser.add_argument("--complete-module", help=argparse.SUPPRESS)
    parser.add_argument("--complete-testcase", help=argparse.SUPPRESS)

    args = parser.parse_args(argv)

    if args.workdir:
        os.chdir(args.workdir)

    # Make sure the directory we're running from is available
    sys.path.insert(1, os.getcwd())

    try:
        if args.complete_module is not None:
            for compl in complete_module(args.complete_module):
                print(compl)
            return

        if args.complete_testcase is not None:
            for compl in complete_testcase(args.complete_testcase):
                print(compl)
            return
    except Exception:
        # Silently drop these exceptions to not disturb commandline completion
        sys.exit(1)

    import tbot
    import tbot.log
    import tbot.log_event

    for flag in args.flags:
        if "=" in flag:
            (flag_name, value) = flag.split("=", 1)
        else:
            flag_name = flag
            value = True
        tbot.flags[flag_name] = value

    tbot.log.message(f"flags: {tbot.flags}")

    if args.json_log_stream:
        tbot.log.LOGFILE = open(args.json_log_stream, "w")

    tbot.log.VERBOSITY = tbot.log.Verbosity(
        tbot.log.Verbosity.STDOUT + args.verbosity - args.quiet
    )

    tbot.log_event.tbot_start()

    # Initialize tbot context with our settings
    tbot.ctx = tbot.Context(add_defaults=True, keep_alive=args.keep_alive)

    if args.lab is not None:
        load_config(args.lab, tbot.ctx)
    if args.board is not None:
        load_config(args.board, tbot.ctx)
    for config in args.config:
        load_config(config, tbot.ctx)

    try:
        with tbot.ctx:
            for testcase in args.testcase:
                run_testcase(testcase)
    except Exception as e:
        import traceback

        trace = traceback.format_exc(limit=-6)
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
