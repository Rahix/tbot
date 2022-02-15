import hashlib
import os
import select
import time
from typing import List, Optional, Tuple, TypeVar

import tbot
from tbot import machine
from tbot.machine import channel, linux

BH = TypeVar("BH", bound=linux.LinuxShell)

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

# Open fifos for reading AND writing to make sure that we can
# never receive EOF (which would happen when no reader fds are open)
cat <&10 1<>{fifo_console_recv} &
cat 0<>{fifo_console_send} >&11 &

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

# Open for reading and writing so the fifo can never receive EOF
cat <>{fifo_commands}
# If something goes wrong, send an invalid command to abort
echo "FAIL"
""",
}


@tbot.named_testcase("uboot_setup_testhooks")
def setup_testhooks(
    bh: BH, m_console: BH, m_command: BH
) -> Tuple[channel.Channel, channel.Channel]:
    """
    Setup u-boot-test-* hook scripts for tbot interaction.

    The scripts use 3 FIFOs for sending/receiving the console data to/from tbot
    which in turn communicates with the board.  The third FIFO is used for
    commands (currently only RESET).

    This testcase tries to be smart and only rewrite the hooks when something
    changed.  For this purpose a hash-value is stored on the build-host and
    checked agains the locally computed one.
    """

    # m_console and m_command must not be the same machine
    assert id(m_console) != id(m_command), "testhook channels must be separate"

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
        fifos[fifoname] = fifo.at_host(bh)
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
    bh.env("PATH", f"{hookdir.at_host(bh)}:{oldpath}")

    tbot.log.message("Open console & command channels ...")
    chan_console = m_console.open_channel(hookdir / "tbot-console")
    chan_command = m_command.open_channel(hookdir / "tbot-commands")

    return (chan_console, chan_command)


@tbot.named_testcase("uboot_testpy")
def testpy(
    uboot_sources: linux.Path[BH],
    *,
    board: Optional[tbot.role.Board] = None,
    uboot: Optional[tbot.role.BoardUBoot] = None,
    boardenv: Optional[str] = None,
    testpy_args: Optional[List[str]] = None,
) -> None:
    """
    Run U-Boot's test/py test-framework against a tbot-machine.

    .. note::

        This function supersedes the old :py:func:`tbot.tc.uboot.testpy`
        testcase.  Please read the docs below carefully on how to use it.

    This function is meant to be integrated into a custom testcase for test/py
    which sets up the environment as needed.  A simple example could look like
    this:

    .. code-block:: python

        from tbot_contrib import uboot

        BOARDENV = r\"""# Boardenv for xyz board.

        env__net_dhcp_server = True
        \"""

        @tbot.testcase
        def run_testpy() -> None:
            with tbot.ctx.request(tbot.role.BuildHost) as h:
                # location of the U-Boot sources - these must have been
                # pre-configured elsewhere (or configured here manually)
                build_dir = h.workdir / "u-boot-mainline"

                # subshell for the build environment
                with h.subshell():
                    # setup toolchain
                    h.env("CROSS_COMPILE", "arm-linux-")

                    # if needed, you could configure sources here
                    # h.exec0("make", "xyz_defconfig")

                    uboot.testpy(
                        build_dir,
                        boardenv=BOARDENV,
                        testpy_args=["--maxfail", "6"],
                    )

    As shown above, the testcase will attempt to instanciate the default board
    machine from :py:class:`tbot.role.Board` and
    :py:class:`tbot.role.BoardUBoot`.  If a different board machine should be
    used, it can be passed in explicitly like this:

    .. code-block:: python

        @tbot.testcase
        def run_testpy() -> None:
            with tbot.ctx() as cx:
                h = cx.request(tbot.role.BuildHost)
                build_dir = ...
                ...

                # for demonstration - this is exactly what uboot.testpy()
                # would do on its own when board and uboot are not passed.
                b = cx.request(tbot.role.Board)
                ub = cx.request(tbot.role.BoardUBoot, exclusive=True)

                uboot.testpy(
                    build_dir,
                    board=b,
                    uboot=ub,
                    boardenv=BOARDENV,
                )

    It is advisable to request the U-Boot machine with ``exclusive=True`` so no
    other code will attempt interacting with it while testpy is running. This
    is not a hard requirement, though.

    :param tbot.machine.linux.Path uboot_sources: Path to the U-Boot sources on
        the host where test/py should run.  This could, for example, be your
        build-host.  Importantly, before calling ``testpy()``, you must ensure
        that these U-Boot sources have been configured appropriately for your
        board.  ``testpy()`` will make no attempt to do this itself.
    :param tbot.role.Board board:  Optional board machine if requesting
        :py:class:`tbot.role.Board` is not enough.  ``uboot`` must also be
        passed if ``board`` is passed.
    :param tbot.role.BoardUBoot uboot:  Optional U-Boot machine if requesting
        :py:class:`tbot.role.BoardUBoot` is not enough.  ``board`` must also be
        passed if ``uboot`` is passed.
    :param str boardenv: Optional "boardenv" file contents to configure
        test/py.  This can, for example, be used to configure where mmc tests
        can perform test reads.  The individual test implementations in the
        U-Boot sources document available options.
    :param list(str) testpy_args: Optional additional args to be passed to the
        test/py invocation.  For example, you can use ``["-k", "mmc"]`` to
        filter for mmc tests only.  Or ``["-v"]`` to show the names of all
        testcases as they are executed (or skipped).

    .. versionadded:: 0.9.5
    """
    if board is not None:
        assert uboot is not None, "when passing `board`, `uboot` is also required!"

    with tbot.ctx() as cx:
        bh = uboot_sources.host

        with tbot.ctx.request(tbot.role.LabHost) as lh:
            if id(bh) == id(lh):
                tbot.log.warning(
                    "The host we're using for test/py might"
                    + " be needed elsewhere during the test run."
                    + "  Creating a clone..."
                )
                bh: BH = cx.enter_context(bh.clone())  # type: ignore

        # Spawn a subshell to not mess up the parent shell's environment and PWD
        cx.enter_context(bh.subshell())

        m_console: BH = cx.enter_context(bh.clone())  # type: ignore
        m_command: BH = cx.enter_context(bh.clone())  # type: ignore
        chan_console, chan_command = setup_testhooks(bh, m_console, m_command)

        assert (
            uboot_sources / ".config"
        ).exists(), "u-boot does not seem configured (.config is missing)!"
        assert (
            uboot_sources / "include" / "autoconf.mk"
        ).exists(), "include/autoconf.mk is missing!"

        if board is not None:
            b = board
        else:
            b = cx.request(tbot.role.Board, reset=True)

        assert isinstance(
            b, machine.board.PowerControl
        ), "board does not support power-control!"

        if board is not None:
            assert uboot is not None  # for type checking
            ub = uboot
        else:
            ub = cx.request(tbot.role.BoardUBoot, exclusive=True)

        chan_uboot = ub.ch

        boardtype = "unknown"
        if boardenv is not None:
            boardtype = f"tbot-{b.name}"
            boardtype_filename = boardtype.replace("-", "_")
            boardenv_file = (
                uboot_sources
                / "test"
                / "py"
                / f"u_boot_boardenv_{boardtype_filename}.py"
            )
            boardenv_file.write_text(boardenv)

        bh.exec0("cd", uboot_sources)
        chan_testpy = cx.enter_context(
            bh.run(
                "./test/py/test.py",
                "--build-dir",
                ".",
                "--board-type",
                boardtype,
                *(testpy_args or []),
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

        try:
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
                        if b.powercycle_delay > 0:
                            time.sleep(b.powercycle_delay)
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
        except KeyboardInterrupt:
            # on keyboard interrupt, try to abort test/py
            chan_testpy.sendcontrol("C")
            chan_testpy.terminate()
            raise
