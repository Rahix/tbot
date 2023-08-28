# tbot, Embedded Automation Tool
# Copyright (C) 2019  Harald Seiler
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import string
import sys
import os
import pathlib
import argparse
import inspect
import tbot.error
import typing
from typing import List

try:
    from tbot import _version  # type: ignore
except ImportError:

    class _version:  # type: ignore
        version = "unknown"


# Highlighter {{{
def _import_hightlighter() -> typing.Callable[[str], str]:
    """
    Attempt importing pygments and if that fails use a fall back implementation.

    The reason for this to be a function is to minimize startup time and only
    import pygments if it is actually needed.
    """
    from tbot import log

    if not log.IS_COLOR:
        return lambda s: s

    try:
        highlight = __import__("pygments").highlight  # type: ignore
        lexer = __import__("pygments.lexers").lexers.PythonLexer  # type: ignore
        formatter = __import__(  # type: ignore
            "pygments.formatters"
        ).formatters.TerminalFormatter

        return lambda s: typing.cast(str, highlight(s, lexer(), formatter()).strip())
    except ImportError:
        return lambda s: str(log.c(s).bold.yellow)


# }}}


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


def main() -> None:  # noqa: C901
    """Tbot main entry point."""

    # ArgumentParser {{{
    parser = TbotArgumentParser(
        prog="tbot",
        description="Test and development automation tool, tailored for embedded",
        fromfile_prefix_chars="@",
    )

    parser.add_argument("testcase", nargs="*", help="testcase that should be run.")

    parser.add_argument(
        "-C",
        metavar="WORKDIR",
        dest="workdir",
        help="use WORKDIR as working directory instead of the current directory.",
    )

    parser.add_argument("-b", "--board", help="use this board instead of the default.")

    parser.add_argument("-l", "--lab", help="use this lab instead of the default.")

    parser.add_argument(
        "-T",
        metavar="TC-DIR",
        dest="tcdirs",
        action="append",
        default=[],
        help="add a directory to the testcase search path.",
    )

    parser.add_argument(
        "-t",
        metavar="TC-FILE",
        dest="tcfiles",
        action="append",
        default=[],
        help="add a file to the testcase search path.",
    )

    parser.add_argument(
        "-f",
        metavar="FLAG",
        dest="flags",
        action="append",
        default=[],
        help="set a user defined flag to change testcase behaviour",
    )

    parser.add_argument(
        "-p",
        metavar="NAME=VALUE",
        dest="params",
        action="append",
        default=[],
        help="set a testcase parameter, value is parsed using `eval`",
    )

    parser.add_argument(
        "-v", dest="verbosity", action="count", default=0, help="increase the verbosity"
    )

    parser.add_argument(
        "-q", dest="quiet", action="count", default=0, help="decrease the verbosity"
    )

    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {_version.version}"
    )

    parser.add_argument(
        "--log", metavar="LOGFILE", help="Write a log to the specified file"
    )

    parser.add_argument(
        "--log-auto",
        action="store_true",
        help="Write a log to `log/<lab>-<board>-NNNN.json`",
    )

    flags = [
        (["--list-testcases"], "list all testcases in the current search path."),
        (["--list-files"], "list all testcase files."),
        (["--list-flags"], "list all flags defined in lab or board config."),
        (["-s", "--show"], "show testcase signatures instead of running them."),
        (["-i", "--interactive"], "prompt before running each command."),
    ]

    for flag_names, flag_help in flags:
        parser.add_argument(*flag_names, action="store_true", help=flag_help)

    # }}}

    args = parser.parse_args()

    if args.workdir:
        os.chdir(args.workdir)

    from tbot import log, log_event

    # Logging {{{
    # Determine log-file location
    if args.log_auto:
        logdir = pathlib.Path.cwd() / "log"
        logdir.mkdir(exist_ok=True)

        lab_name = "none" if args.lab is None else pathlib.Path(args.lab).stem
        board_name = "none" if args.board is None else pathlib.Path(args.board).stem

        prefix = f"{lab_name}-{board_name}"
        glob_pattern = f"{prefix}-*.json"
        new_num = sum(1 for _ in logdir.glob(glob_pattern)) + 1
        logfile = logdir / f"{prefix}-{new_num:04}.json"
        # Ensure logfile will not overwrite another one
        while logfile.exists():
            new_num += 1
            logfile = logdir / f"{prefix}-{new_num:04}.json"

        log.LOGFILE = open(logfile, "w")
    elif args.log:
        log.LOGFILE = open(args.log, "w")

    # Set verbosity
    log.VERBOSITY = log.Verbosity(log.Verbosity.INFO + args.verbosity - args.quiet)

    # Enable interactive mode
    if args.interactive:
        log.INTERACTIVE = True

        # Verbosity has to be at least command level
        log.VERBOSITY = max(log.VERBOSITY, log.Verbosity.COMMAND)
    # }}}

    import tbot
    from tbot import loader

    for flag in args.flags:
        tbot.flags.add(flag)

    if args.list_testcases or args.list_files:
        log.VERBOSITY = -1  # type: ignore
    else:
        log_event.tbot_start()

    # Load testcases {{{
    if "TBOTPATH" in os.environ:
        environ_paths = os.environ["TBOTPATH"].split(":")
    else:
        environ_paths = []

    files = loader.get_file_list(
        (pathlib.Path(d).resolve() for d in environ_paths),
        (pathlib.Path(d).resolve() for d in args.tcdirs),
        (pathlib.Path(f).resolve() for f in args.tcfiles),
    )

    if args.list_files:
        for f in files:
            print(f"{f}")
        return

    testcases = loader.collect_testcases(files)

    if args.list_testcases:
        for tc in testcases:
            print(tc)
        return

    if args.show:
        import textwrap

        highlight = _import_hightlighter()

        for i, name in enumerate(args.testcase):
            if i != 0:
                print(log.c("\n=================================\n").dark)
            func = testcases[name]
            signature = f"def {name}{str(inspect.signature(func))}:\n    ..."
            print(highlight(signature))
            print(log.c(f"----------------").dark)
            print(
                log.c(
                    textwrap.dedent(func.__doc__ or "No docstring available.").strip()
                ).green
            )
        return
    # }}}

    # Load configs {{{
    # Set the actual selected types, needs to be ignored by mypy
    # beause this is obviously not good python
    lab = None
    if args.lab is not None:
        lab = loader.load_module(pathlib.Path(args.lab).resolve())
        if hasattr(lab, "register_machines"):
            getattr(lab, "register_machines")(tbot.ctx)
        else:
            tbot.ctx.register(getattr(lab, "LAB"), [tbot.role.LabHost])

        # Needed to make legacy tbot.selectable module work
        tbot.selectable.LabHost = tbot.ctx._roles[tbot.role.LabHost]  # type: ignore
    else:
        pass

    board = None
    if args.board is not None:
        board = loader.load_module(pathlib.Path(args.board).resolve())
        if hasattr(board, "register_machines"):
            getattr(board, "register_machines")(tbot.ctx)
        else:
            if hasattr(board, "BOARD"):
                tbot.ctx.register(getattr(board, "BOARD"), [tbot.role.Board])
            if hasattr(board, "UBOOT"):
                tbot.ctx.register(getattr(board, "UBOOT"), [tbot.role.BoardUBoot])
            if hasattr(board, "LINUX"):
                tbot.ctx.register(getattr(board, "LINUX"), [tbot.role.BoardLinux])

        # Needed to make legacy tbot.selectable module work
        if tbot.role.Board in tbot.ctx._roles:
            tbot.selectable.Board = tbot.ctx._roles[tbot.role.Board]  # type: ignore
        if tbot.role.BoardUBoot in tbot.ctx._roles:
            tbot.selectable.UBootMachine = tbot.ctx._roles[tbot.role.BoardUBoot]  # type: ignore
        if tbot.role.BoardLinux in tbot.ctx._roles:
            tbot.selectable.LinuxMachine = tbot.ctx._roles[tbot.role.BoardLinux]  # type: ignore
    else:
        pass

    if args.list_flags:
        all_flags: typing.Dict[str, str] = dict()
        if lab is not None and "FLAGS" in lab.__dict__:
            all_flags.update(lab.__dict__["FLAGS"])

        if board is not None and "FLAGS" in board.__dict__:
            all_flags.update(board.__dict__["FLAGS"])

        width = max(map(len, flags))
        for name, description in all_flags.items():
            log.message(log.c(name.ljust(width)).blue + ": " + description)
    # }}}

    # Testcase Parameters {{{
    parameters = {}
    for param in args.params:
        name, eval_code = param.split("=", maxsplit=1)
        parameters[name] = eval(eval_code)

    if parameters != {}:
        highlight = _import_hightlighter()
        tbot.log.message(
            tbot.log.c("Parameters:\n").bold
            + "\n".join(
                f"    {name:10} = " + highlight(f"{value!r}")
                for name, value in parameters.items()
            )
        )
    # }}}

    if len(tbot.flags) != 0:
        highlight = _import_hightlighter()
        tbot.log.message(
            tbot.log.c("Flags:\n").bold
            + ", ".join(highlight(f"{flag!r}") for flag in tbot.flags)
        )

    try:
        with tbot.ctx:
            for tc in args.testcase:
                func = testcases[tc]

                if len(args.testcase) == 1:
                    params = parameters
                else:
                    # Filter parameter list if multiple testcases are scheduled to run

                    try:
                        func_code = getattr(func, "__wrapped__").__code__
                    except AttributeError:
                        func_code = func.__code__
                    # Get list of argument names
                    argspec = inspect.getargs(func_code)

                    params = {}
                    for name, value in parameters.items():
                        if argspec.varkw is not None or name in argspec.args:
                            params[name] = value
                        else:
                            tbot.log.warning(
                                f"Parameter {name!r} not defined for testcase {tc!r}, ignoring ..."
                            )

                func(**params)
    except Exception as e:  # noqa: E722
        import traceback

        trace = traceback.format_exc()
        log_event.exception(e.__class__.__name__, trace)
        log_event.tbot_end(False)
        sys.exit(1)
    except KeyboardInterrupt:
        log_event.exception("KeyboardInterrupt", "Test run manually aborted.")
        log_event.tbot_end(False)
        sys.exit(130)
    else:
        log_event.tbot_end(True)


if __name__ == "__main__":
    main()


# vim: foldmethod=marker foldmarker={{{,}}}
