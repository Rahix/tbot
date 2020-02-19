import contextlib
import hashlib
import os
import select
import typing

import tbot
from tbot.machine import board, channel, linux
from tbot.tc import uboot as uboot_tc

BH = typing.TypeVar("BH", bound=linux.Builder)

HOOK_SCRIPTS = {
    # Hook which test/py uses to access the console:
    "u-boot-test-console": """\
#!/usr/bin/env bash

stty raw -echo

exec 10<&0
exec 11>&1

cat <&10 >{fifo_console_send} &
cat <{fifo_console_recv} >&11 &

sleep infinity
""",
    # Script which tbot uses to 'emulate' the console:
    "tbot-console": """\
#!/usr/bin/env bash

stty raw -echo

exec 10<&0
exec 11>&1

while true; do cat <&10 >{fifo_console_recv}; done &
while true; do cat <{fifo_console_send} >&11; done &

sleep infinity
""",
    # Hook which test/py uses to reset the board
    "u-boot-test-reset": """\
#!/usr/bin/env bash

echo "RESET" >{fifo_commands}
""",
    # Hook which test/py calls to flash U-Boot (unused here)
    "u-boot-test-flash": """\
#!/usr/bin/env bash
""",
    # Script which tbot uses to listen to incoming commands
    # (only for triggering resets at the moment)
    "tbot-commands": """\
#!/usr/bin/env bash

while true; do cat {fifo_commands}; done
""",
}


@tbot.named_testcase("uboot_setup_testhooks")
def setup_testhooks(
    bh: BH, m_console: BH, m_command: BH
) -> typing.Tuple[channel.Channel, channel.Channel]:
    """
    Setup u-boot-test-* hook scripts for tbot interaction.
    """

    hookdir = bh.workdir / "uboot-testpy-tbot"
    if not hookdir.is_dir():
        bh.exec0("mkdir", hookdir)

    # FIFOs --- {{{
    tbot.log.message("Creating FIFOs ...")

    # This dict is used for resolving the paths in the scripts later on
    fifos = {}
    for fifoname in ["fifo_console_send", "fifo_console_recv", "fifo_commands"]:
        fifo = hookdir / fifoname
        bh.exec0("rm", "-rf", fifo)
        bh.exec0("mkfifo", fifo)
        fifos[fifoname] = fifo._local_str()
    # }}}

    # Hook Scripts --- {{{

    # Generate a hash for the version of the control files
    script_hasher = hashlib.sha256()
    for script in sorted(HOOK_SCRIPTS.values()):
        script_hasher.update(script.encode("utf-8"))
    script_hash = script_hasher.hexdigest()

    hashfile = hookdir / "tbot-scripts.sha256"
    try:
        up_to_date = script_hash == hashfile.read_text().strip()
    except Exception:
        up_to_date = False

    if up_to_date:
        tbot.log.message("Hooks are up to date, skipping deployment ...")
    else:
        tbot.log.message("Updating hook scripts ...")

        for scriptname, script in HOOK_SCRIPTS.items():
            rendered = script.format(**fifos)
            (hookdir / scriptname).write_text(rendered)
            bh.exec0("chmod", "+x", hookdir / scriptname)

        # Write checksum so we don't re-deploy next time
        hashfile.write_text(script_hash)
    # }}}

    tbot.log.message("Adding hooks to $PATH ...")
    oldpath = bh.env("PATH")
    bh.env("PATH", f"{hookdir._local_str()}:{oldpath}")

    tbot.log.message("Open console & command channels ...")
    chan_console = m_console.open_channel(hookdir / "tbot-console")
    chan_command = m_command.open_channel(hookdir / "tbot-commands")

    return (chan_console, chan_command)


@tbot.named_testcase("uboot_testpy")
@tbot.with_lab
def testpy(
    lh: linux.Lab,
    *,
    build_host: typing.Optional[linux.Builder] = None,
    uboot_builder: typing.Optional[uboot_tc.UBootBuilder] = None,
    boardenv: typing.Optional[str] = None,
    testpy_args: typing.List[str] = [],
) -> None:
    with contextlib.ExitStack() as cx:
        if build_host is not None:
            bh = cx.enter_context(build_host)
        else:
            bh = cx.enter_context(lh.build())

        # Spawn a subshell to not mess up the parent shell's environment and PWD
        cx.enter_context(bh.subshell())

        chan_console, chan_command = setup_testhooks(
            bh, cx.enter_context(bh.clone()), cx.enter_context(bh.clone())
        )

        if uboot_builder is None:
            builder = uboot_tc.UBootBuilder._get_selected_builder()
        else:
            builder = uboot_builder

        uboot_repo = uboot_tc.checkout(builder, clean=False, host=bh)

        # test/py wants to read U-Boot's config.  Run the builder's configure
        # step if no `.config` is available and then also generate `autoconf.mk`.
        dotconfig_missing = not (uboot_repo / ".config").exists()
        autoconfmk_missing = not (uboot_repo / "include" / "autoconf.mk").exists()

        if dotconfig_missing or autoconfmk_missing:
            with tbot.testcase("uboot_configure"), builder.do_toolchain(bh):
                tbot.log.message("Configuring U-Boot checkout ...")
                bh.exec0("cd", uboot_repo)

                if dotconfig_missing:
                    builder.do_configure(bh, uboot_repo)

                if autoconfmk_missing:
                    bh.exec0("make", "include/autoconf.mk")

        # Initialize the board
        # TODO: Add a parameter to allow passing in a board
        b = cx.enter_context(tbot.acquire_board(lh))  # type: ignore
        assert isinstance(b, board.PowerControl)
        ub = cx.enter_context(tbot.acquire_uboot(b))
        chan_uboot = ub.ch

        # If a boardenv was passed in, copy it to the build-host and set
        # a board-type to make test/py pick it up.
        board_type = "unknown"
        if boardenv is None:
            # If no explicit boardenv was given, maybe the builder has one.
            try:
                boardenv = getattr(builder, "testpy_boardenv")
            except AttributeError:
                pass
        if boardenv is not None:
            board_type = f"tbot-{b.name}"
            bt_filename = board_type.replace("-", "_")
            be_file = uboot_repo / "test" / "py" / f"u_boot_boardenv_{bt_filename}.py"

            be_file.write_text(boardenv)

        # Start test/py as an interactive command
        bh.exec0("cd", uboot_repo)
        chan_testpy = cx.enter_context(
            bh.run(
                "./test/py/test.py",
                "--build-dir",
                ".",
                "--board-type",
                board_type,
                *testpy_args,
            )
        )

        # We have to deal with incoming data on any of the following channels.
        # The comments denote what needs to be done for each channel:
        readfds = [
            chan_console,  # Send data to U-Boot
            chan_uboot,  # Send data to chan_console (test/py)
            chan_command,  # Powercycle the board
            chan_testpy,  # Read data so the log-event picks it up
        ]

        while True:
            r, _, _ = select.select(readfds, [], [])

            if chan_console in r:
                # Send data to U-Boot
                data = os.read(chan_console.fileno(), 4096)
                os.write(chan_uboot.fileno(), data)
            if chan_uboot in r:
                # Send data to chan_console (test/py)
                data = os.read(chan_uboot.fileno(), 4096)
                os.write(chan_console.fileno(), data)
            if chan_command in r:
                # Powercycle the board
                msg = chan_command.read()

                if msg[:2] == b"RE":
                    b.poweroff()
                    b.poweron()
                else:
                    raise Exception(f"Got unknown command {msg!r}!")
            if chan_testpy in r:
                # Read data so the log-event picks it up.  If a
                # DeathStringException occurs here, test/py finished and we
                # need to properly terminate the LinuxShell.run() context.
                try:
                    chan_testpy.read()
                except linux.CommandEndedException:
                    chan_testpy.terminate0()
                    break
