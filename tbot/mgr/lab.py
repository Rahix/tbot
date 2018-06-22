import sys
import string
import typing
import pathlib
import argparse

TEMPLATE = string.Template(
    """\
\"\"\"
$headername Lab Config
\"\"\"
import pathlib
from tbot.config import Config


def config(cfg: Config) -> None:
    \"\"\" Lab config \"\"\"
    username = $username

    cfg["lab"] = {
        "name": "$labname",
        # Hostname/IP of this labhost
        "hostname": "$hostname",
        # Optional port
        # "port": 22,
        # User for logging in
        "user": username,
        # Password/Keyfile for authenticating
        "$ctype": $cred,
    }

    # A directory on the labhost where TBot can store files
    cfg["tbot.workdir"] = $workdir

    # Configuration for buildhosts
    cfg["build"] = {
        # Default buildhost that will be used if no other is specified
        "default": "$labname",
        # Buildhost that is the labhost, needed for U-Boot tests
        "local": "$labname",
        # $labname (local) buildhost
        "$labname": {
            # Same credentials as before. Add a custom ssh command with a keyfile
            # that requires no password if you don't have passwordless login on
            # localhost on the labhost by default
            "username": username,
            "hostname": "localhost",
            # We can build in a subdir of our workdir
            "workdir": cfg["tbot.workdir"] / "tbot-build",
            # Toolchains available on this host
            "toolchains": {$toolchains
                # "toolchain-name": {
                #     # A script that will set environment variables for this toolchain
                #     # eg. $$ARCH, $$CC, $$CFLAGS, ...
                #     "env_setup_script": pathlib.PurePosixPath("/path/to/tc-setup-script"),
                # },
            },
        },
        # Add another buildhost here if you want to build on a different machine than the labhost
    }
"""
)


def add_lab(
    *,
    file: pathlib.Path,
    name: str,
    username: typing.Optional[str] = None,
    hostname: str,
    ctype: typing.Optional[str] = None,
    cred: typing.Optional[str] = None,
    workdir: typing.Optional[str] = None,
    toolchains: str = "",
) -> None:
    filename = file.stem

    headername = name.title() if name[:3].isalpha() else name
    if filename != name:
        headername += f" ({filename})"

    if username is None:
        username = '__import__("getpass").getuser()'
    else:
        username = repr(username)

    if workdir is not None:
        workdir = f'"{workdir}"'
    else:
        workdir = 'f"/tmp/{username}-tbot"'

    workdir = f"pathlib.PurePosixPath({workdir})"

    src = TEMPLATE.substitute(
        labname=name,
        headername=headername,
        username=username,
        hostname=hostname,
        ctype=ctype or "keyfile",
        cred=cred or 'pathlib.Path.home() / ".ssh" / "id_rsa"',
        workdir=workdir,
        toolchains=toolchains,
    )

    with open(file, mode="w") as f:
        f.write(src)

    print(f"Config for {name} written to {file}")


def add_lab_dummy_cmd(args: argparse.Namespace) -> None:
    name = args.name or "dummy-lab"
    file = pathlib.Path.cwd() / "config" / "labs" / f"{name}.py"

    if file.exists() and not args.force:
        print(f"Lab {args.filename} already exists!")
        sys.exit(1)

    add_lab(
        file=file,
        name=name,
        hostname="localhost",
        toolchains="""
                "dummy-toolchain": {
                    "env_setup_script": pathlib.PurePosixPath("/dev/null"),
                },""",
    )


def add_lab_cmd(args: argparse.Namespace) -> None:
    if args.filename is None:
        if args.interactive:
            args.filename = input("Filename for the lab: ")
        else:
            print("Filename required! (or interactive mode (-i))")
            sys.exit(1)
    file = pathlib.Path.cwd() / "config" / "labs" / f"{args.filename}.py"
    if file.exists() and not args.force:
        print(f"Lab {args.filename} already exists!")
        sys.exit(1)

    if args.name is None and args.interactive:
        name = input("Name to be used in config (leave empty for same as filename): ")
        if name != "":
            args.name = name

    if args.host is None:
        if args.interactive:
            args.host = input("Hostname of the lab: ")
        else:
            print("A hostname is required!")
            sys.exit(1)

    if args.user is None and args.interactive:
        user = input("Username on the labhost (leave empty for local username): ")
        if user != "":
            args.user = user

    ctype = "keyfile"
    cred = None

    if args.keyfile:
        cred = args.keyfile

    if args.password:
        ctype = "password"
        cred = repr(args.password)

    if cred is None and args.interactive:
        password = input(
            "Password for logging onto the labhost (leave empty to use keyfile): "
        )
        if password == "":
            keyfile = input("Custom keyfile (leave empty for default): ")
            ctype = "keyfile"
            if keyfile == "":
                cred = None
            else:
                cred = f"pathlib.Path({keyfile!r}).expanduser()"
        else:
            ctype = "password"
            cred = repr(password)

    if args.workdir is None and args.interactive:
        wd = input("Workdir on the labhost (leave empty for /tmp): ")
        if wd != "":
            args.workdir = wd

    add_lab(
        file=file,
        name=args.name or args.filename,
        username=args.user,
        hostname=args.host,
        ctype=ctype,
        cred=cred,
        workdir=args.workdir,
    )
