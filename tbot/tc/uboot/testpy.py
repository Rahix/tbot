# tbot, Embedded Automation Tool
# Copyright (C) 2020  Harald Seiler
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

import contextlib
import hashlib
import os
import select
import typing
import time

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
) -> typing.Tuple[channel.Channel, channel.Channel]:
    """
    Setup u-boot-test-* hook scripts for tbot interaction.

    The scripts use 3 FIFOs for sending/receiving the console data to/from tbot
    which in turn communicates with the board.  The third FIFO is used for
    commands (currently only RESET).

    This testcase tries to be smart and only rewrite the hooks when something
    changed.  For this purpose a hash-value is stored on the build-host and
    checked agains the locally computed one.
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
@tbot.with_lab
def testpy(
    lh: linux.Lab,
    *,
    build_host: typing.Optional[linux.Builder] = None,
    uboot_builder: typing.Optional[uboot_tc.UBootBuilder] = None,
    boardenv: typing.Optional[str] = None,
    testpy_args: typing.List[str] = [],
) -> None:
    """
    Run U-Boot's test/py test-framework against the selected board.

    This testcase can be called from the command-line as ``uboot_testpy``.

    :param tbot.machine.linux.Builder build_host: Optional build-host where
        U-Boot should be built (and in this case, where test/py will run).  By
        default, ``tbot.acquire_lab().build()`` is used.
    :param tbot.tc.uboot.UBootBuilder uboot_builder: Optional configuration for
        U-Boot checkout.  By default, ``tbot.acquire_uboot().build`` is used
        (exactly like ``uboot_build`` does).
    :param str boardenv: Optional contents for the ``boardenv.py`` file.  If
        this option is not given, ``UBootBuilder.testpy_boardenv`` is used (or
        nothing).
    :param list(str) testpy_args: Additional arguments to be passed to test/py.
        Can be used, for example, to limit which tests should be run (using
        ``testpy_args=["-k", "sf"]``).

    **Example**:

    The following additions to a board-config make it possible to call
    ``tbot ... -vv uboot_testpy``:

    .. code-block:: python

        from tbot.tc import uboot

        class DHComUBootBuilder(uboot.UBootBuilder):
            name = "dhcom-pdk2"
            defconfig = "dh_imx6_defconfig"
            toolchain = "imx6q"

            testpy_boardenv = r\"""# Config for dhcom pdk2 board

        # A list of sections of Flash memory to be tested.
        env__sf_configs = (
            {
                # Where in SPI Flash should the test operate.
                'offset': 0x140000,
                # This value is optional.
                #   If present, specifies if the test can write to Flash offset
                #   If missing, defaults to False.
                'writeable': True,
            },
        )
        \"""


        class DHComUBoot(board.Connector, board.UBootShell):
            name = "dhcom-uboot"
            prompt = "=> "

            # Don't forget this!
            build = DHComUBootBuilder()
    """
    with contextlib.ExitStack() as cx:
        if build_host is not None:
            bh = cx.enter_context(build_host)
        else:
            bh = cx.enter_context(lh.build())
            if bh is lh:
                tbot.log.warning(
                    """\
The build() method for the selected lab should not return `self` but instead `self.clone()`.

    Otherwise, `uboot_testpy` might not be able to run test/py in parallel to switching board
    power.

    Attempting to call build_host.clone() automatically now ..."""
                )
                bh = cx.enter_context(bh.clone())

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
