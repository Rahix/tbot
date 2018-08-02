"""
TBot Config Manager
-------------------

A tool to manage the configuration for a tbot project
"""
import sys
import argparse

from tbot.mgr.new import new_or_init_cmd
from tbot.mgr.delete import del_cmd
from tbot.mgr.board import add_board_cmd, add_board_dummy_cmd
from tbot.mgr.lab import add_lab_cmd, add_lab_dummy_cmd


def main() -> None:
    """ Main entr point of tbot-mgr """
    parser = argparse.ArgumentParser(
        prog="tbot-mgr", description="Config manager for TBot"
    )

    subparsers = parser.add_subparsers(dest="cmd")

    # ------------- COMMON -------------
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument(
        "-s",
        "--no-interactive",
        "--script-mode",
        help="Disable interactive mode",
        dest="interactive",
        action="store_false",
        default=True,
    )
    common_parser.add_argument(
        "-f",
        "--force",
        help="Overwrite existing board",
        action="store_true",
        default=False,
    )

    # ------------- NEW -------------
    new_parser = subparsers.add_parser(
        "new",
        help="Create a new directory with TBot config files",
        parents=[common_parser],
    )
    new_parser.add_argument("dirname", help="Name of the directory to create")

    # ------------- INIT -------------
    subparsers.add_parser(
        "init",
        help="Create TBot config files in the current directory",
        parents=[common_parser],
    )

    # ------------- DELETE -------------
    del_parser = subparsers.add_parser("del", help="Delete a board/lab")
    del_subparsers = del_parser.add_subparsers(dest="del_cmd")

    del_board_parser = del_subparsers.add_parser("board", help="Delete a board")
    del_board_parser.add_argument("name", help="Name of the board to be deleted")

    del_lab_parser = del_subparsers.add_parser("lab", help="Delete a lab")
    del_lab_parser.add_argument("name", help="Name of the lab to be deleted")

    # ------------- ADD -------------
    add_parser = subparsers.add_parser(
        "add", help="Add a new board/lab to the config in the current directory"
    )
    add_subparsers = add_parser.add_subparsers(dest="add_cmd")

    # ------------- ADD BOARD -------------
    add_board_parser = add_subparsers.add_parser(
        "board",
        help="Add a new board to the config in the current directory",
        parents=[common_parser],
    )
    add_board_parser.add_argument("filename", help="Name of the board", nargs="?")
    add_board_parser.add_argument(
        "-n",
        "--name",
        help="Alternative name that will be used in the config instead of the filename",
    )
    add_board_parser.add_argument(
        "-l",
        "--lab",
        help="A lab that this board is available in",
        action="append",
        default=[],
    )
    add_board_parser.add_argument(
        "-d",
        "--default-lab",
        help="Mark this board as being available in the lab that currently exists in the config",
        action="store_true",
        default=False,
    )
    add_board_parser.add_argument("-t", "--toolchain", help="Which toolchain to use")
    add_board_parser.add_argument(
        "-1", "--on", help="Shell-command on the labhost to power board on"
    )
    add_board_parser.add_argument(
        "-0", "--off", help="Shell-command on the labhost to power board off"
    )
    add_board_parser.add_argument(
        "-c", "--connect", help="Shell-command on the labhost to connect to board"
    )

    # ------------- ADD DUMMY BOARD -------------
    add_board_parser = add_subparsers.add_parser(
        "dummy-board",
        help="Add a new dummy board to the config in the current directory",
        parents=[common_parser],
    )
    add_board_parser.add_argument(
        "-n", "--name", help="Optional name (default is 'dummy-board')"
    )
    add_board_parser.add_argument(
        "-l",
        "--lab",
        help="The lab that this board is available in (default is 'dummy-lab')",
    )

    # ------------- ADD LAB -------------
    add_lab_parser = add_subparsers.add_parser(
        "lab",
        help="Add a new lab to the config in the current directory",
        parents=[common_parser],
    )
    add_lab_parser.add_argument("filename", help="Name of the lab", nargs="?")
    add_lab_parser.add_argument("host", help="Hostname/IP of the labhost", nargs="?")
    add_lab_parser.add_argument(
        "-n",
        "--name",
        help="Alternative name that will be used in the config instead of the filename",
    )
    add_lab_parser.add_argument(
        "-u", "--user", help="Username on the labhost, defaults to local user name"
    )
    add_lab_parser.add_argument(
        "-p",
        "--password",
        help="Password for logging in (can be used instead of keyfile)",
    )
    add_lab_parser.add_argument(
        "-k",
        "--keyfile",
        help="Keyfile for passwordless login (can be used instead of password)",
    )
    add_lab_parser.add_argument(
        "-w", "--workdir", help="Directory on the labhost where TBot can store files"
    )

    # ------------- ADD DUMMY LAB -------------
    add_lab_parser = add_subparsers.add_parser(
        "dummy-lab",
        help="Add a new dummy lab to the config in the current directory",
        parents=[common_parser],
    )
    add_lab_parser.add_argument(
        "-n", "--name", help="Optional name (default is 'dummy-lab')"
    )

    # ------------- ADD DUMMY BOARD + LAB -------------
    add_dummies_parser = add_subparsers.add_parser(
        "dummies",
        help="Add a new dummy board and lab to the config in the current directory",
        parents=[common_parser],
    )
    add_dummies_parser.add_argument(
        "-n", "--name", help="Optional name (default is 'dummy-lab'/'dummy-board')"
    )
    add_dummies_parser.add_argument("-l", "--lab", help="DO NOT USE")

    args = parser.parse_args()

    if args.cmd in ["new", "init"]:
        new_or_init_cmd(args)
    elif args.cmd in ["del"]:
        del_cmd(args)
    elif args.cmd in ["add"]:
        if args.add_cmd in ["board"]:
            add_board_cmd(args)
        elif args.add_cmd in ["dummy-board"]:
            add_board_dummy_cmd(args)
        elif args.add_cmd in ["lab"]:
            add_lab_cmd(args)
        elif args.add_cmd in ["dummy-lab"]:
            add_lab_dummy_cmd(args)
        elif args.add_cmd in ["dummies"]:
            n = args.name or "dummy"
            args.name = f"{n}-lab"
            add_lab_dummy_cmd(args)
            args.name = f"{n}-board"
            args.lab = f"{n}-lab"
            add_board_dummy_cmd(args)
        else:
            print("Unknown subcommand (try -h)!")
            sys.exit(1)
    else:
        print("Unknown subcommand (try -h)!")
        sys.exit(1)
