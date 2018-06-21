import sys
import string
import typing
import pathlib
import argparse

TEMPLATE = string.Template(
    """\
\"\"\"
$headername Board Config
\"\"\"
from tbot.config import Config


def config(cfg: Config) -> None:
    \"\"\" Board config \"\"\"

    if cfg["lab.name"] not in [$labnames]:
        raise Exception(\"\"\"board $boardname: Only availabe in $labnames lab(s)!\"\"\")

    cfg["board"] = {
        "name": "$boardname", $toolchain
        "power": {
            "on_command": "$oncommand",
            "off_command": "$offcommand",
        },
        "serial": {
            "name": "serial-$boardname",
            "command": "$connectcommand",
        },
    }
"""
)


def add_board(
    *,
    file: pathlib.Path,
    name: str,
    labs: typing.List[str],
    toolchain: typing.Optional[str] = None,
    oncmd: typing.Optional[str] = None,
    offcmd: typing.Optional[str] = None,
    connectcmd: typing.Optional[str] = None,
) -> None:
    filename = file.stem

    headername = name.title() if name[:3].isalpha() else name
    if filename != name:
        headername += f" ({filename})"

    toolchain_src = ""
    if toolchain is not None:
        toolchain_src = f'\n        "toolchain": "{toolchain}",'

    oncmd = oncmd or "echo 'NO ON COMMAND SET!'; exit 1"
    offcmd = offcmd or "echo 'NO OFF COMMAND SET!'; exit 1"
    connectcmd = connectcmd or "echo 'NO CONNECT COMMAND SET!'; exit 1"

    src = TEMPLATE.substitute(
        boardname=name,
        headername=headername,
        labnames=repr(labs)[1:-1],
        toolchain=toolchain_src,
        oncommand=oncmd,
        offcommand=offcmd,
        connectcommand=connectcmd,
    )

    with open(file, mode="w") as f:
        f.write(src)

    print(f"Config for {name} written to {file}.")


def add_board_cmd(args: argparse.Namespace) -> None:
    if args.filename is None:
        if args.interactive:
            args.filename = input("Filename for the board: ")
        else:
            print("Filename required! (or interactive mode (-i))")
            sys.exit(1)
    file = pathlib.Path.cwd() / "config" / "boards" / f"{args.filename}.py"
    if file.exists() and not args.force:
        print(f"Board {args.filename} already exists!")
        sys.exit(1)

    labs = args.lab
    if args.default_lab:
        available_labs = list((pathlib.Path.cwd() / "config" / "labs").glob("*.py"))
        if available_labs == []:
            print("No lab found that could be used as the default lab")
            sys.exit(1)
        if len(available_labs) > 1:
            print("Multiple labs found, can't decide which is default")
            sys.exit(1)
        labs.append(available_labs[0].stem)

    if labs == []:
        if args.interactive:
            lab = input("Enter the name of the lab where this board is available: ")
            if lab == "":
                print(
                    "This board would not be available in any labs! Please specify a lab."
                )
                sys.exit(1)
            labs.append(lab)
        else:
            print(
                "This board would not be available in any labs! Please specify a lab using -d or -l"
            )
            sys.exit(1)

    if args.toolchain is None and args.interactive:
        toolchain = input(
            "Enter the name of the toolchain for this board (leave empty for none): "
        )
        if toolchain != "":
            args.toolchain = toolchain

    if args.on is None and args.interactive:
        oncmd = input(
            "Enter the command to power ON the board from the labhost  (leave empty for none): "
        )
        if oncmd != "":
            args.on = oncmd
    if args.off is None and args.interactive:
        offcmd = input(
            "Enter the command to power OFF the board from the labhost (leave empty for none): "
        )
        if offcmd != "":
            args.off = offcmd
    if args.connect is None and args.interactive:
        connectcmd = input(
            "Enter the command to connect to the board from the lab    (leave empty for none): "
        )
        if connectcmd != "":
            args.connect = connectcmd

    add_board(
        file=file,
        name=args.name or args.filename,
        labs=labs,
        toolchain=args.toolchain,
        oncmd=args.on,
        offcmd=args.off,
        connectcmd=args.connect,
    )
