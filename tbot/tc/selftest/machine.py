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

import typing
import time
import re
import tbot
from tbot.machine import channel
from tbot.machine import linux
from tbot.machine import board
from tbot.tc import selftest

__all__ = (
    "selftest_machine_reentrant",
    "selftest_machine_labhost_shell",
    "selftest_machine_ssh_shell",
    "selftest_machine_sshlab_shell",
    "selftest_machine_channel",
)


@tbot.testcase
def selftest_machine_reentrant(
    lab: typing.Optional[selftest.SelftestHost] = None,
) -> None:
    """Test if a machine can be entered multiple times."""
    with lab or selftest.SelftestHost() as lh:
        with lh as h1:
            assert h1.exec0("echo", "FooBar") == "FooBar\n"

        with lh as h2:
            assert h2.exec0("echo", "FooBar2") == "FooBar2\n"


@tbot.testcase
def selftest_machine_labhost_shell(
    lab: typing.Optional[selftest.SelftestHost] = None,
) -> None:
    """Test the LabHost's shell."""
    with lab or selftest.SelftestHost() as lh:
        selftest_machine_shell(lh)

        # with lh.clone() as l2:
        #     selftest_machine_channel(l2.ch, False)

        # with lh.clone() as l2:
        #     selftest_machine_channel(l2.ch, True)


@tbot.testcase
def selftest_machine_ssh_shell(
    lab: typing.Optional[selftest.SelftestHost] = None,
) -> None:
    """Test an SSH shell."""
    from tbot.tc.selftest import minisshd

    with lab or selftest.SelftestHost() as lh:
        if not minisshd.check_minisshd(lh):
            tbot.skip("dropbear is not installed so ssh can't be tested")

        with minisshd.minisshd(lh) as ssh:
            selftest_machine_shell(ssh)

            # selftest_machine_channel(ssh.ch, True)


@tbot.testcase
def selftest_machine_sshlab_shell(
    lab: typing.Optional[selftest.SelftestHost] = None,
) -> None:
    """Test an SSH LabHost shell."""
    from tbot.tc.selftest import minisshd

    with lab or selftest.SelftestHost() as lh:
        if not minisshd.check_minisshd(lh):
            tbot.skip("dropbear is not installed so ssh can't be tested")

        with minisshd.minisshd(lh) as ssh:
            ssh.exec0("true")

            if not minisshd.has_paramiko:
                tbot.log.warning("Skipping paramiko test.")
            else:
                tbot.log.message(tbot.log.c("Testing with paramiko ...").bold)
                with minisshd.MiniSSHLabHostParamiko(ssh.port) as slp:
                    selftest_machine_shell(slp)

            tbot.log.message(tbot.log.c("Testing with plain ssh ...").bold)
            with minisshd.MiniSSHLabHostSSH(ssh.port) as sls:
                selftest_machine_shell(sls)


@tbot.testcase
def selftest_machine_shell(m: typing.Union[linux.LinuxShell, board.UBootShell]) -> None:
    # Capabilities
    cap = []
    if isinstance(m, linux.LinuxShell):
        if isinstance(m, linux.Bash):
            cap.extend(["printf", "jobs", "control", "run"])
        # TODO: Re-add when Ash is implemented
        # if m.shell == linux.Ash:
        #     cap.extend(["printf", "control"])

    tbot.log.message("Testing command output ...")
    out = m.exec0("echo", "Hello World")
    assert out == "Hello World\n", repr(out)

    out = m.exec0("echo", "$?", "!#")
    assert out == "$? !#\n", repr(out)

    if "printf" in cap:
        out = m.exec0("printf", "Hello World")
        assert out == "Hello World", repr(out)

        out = m.exec0("printf", "Hello\\nWorld")
        assert out == "Hello\nWorld", repr(out)

        out = m.exec0("printf", "Hello\nWorld")
        assert out == "Hello\nWorld", repr(out)

    s = "_".join(map(lambda i: f"{i:02}", range(80)))
    out = m.exec0("echo", s)
    assert out == f"{s}\n", repr(out)

    tbot.log.message("Testing return codes ...")
    assert m.test("true")
    assert not m.test("false")

    if isinstance(m, linux.LinuxShell):
        tbot.log.message("Testing env vars ...")
        value = "12\nfoo !? # true; exit\n"
        m.env("TBOT_TEST_ENV_VAR", value)
        out = m.env("TBOT_TEST_ENV_VAR")
        assert out == value, repr(out)

        tbot.log.message("Testing redirection (and weird paths) ...")
        f = m.workdir / ".redir test.txt"
        if f.exists():
            m.exec0("rm", f)

        assert (
            m.fsroot / "proc" / "version"
        ).exists(), "/proc/version is missing for some reason ..."

        m.exec0("echo", "Some data - And some more", linux.RedirStdout(f))

        out = m.exec0("cat", f)
        # TODO: Newline
        assert out == "Some data - And some more\n", repr(out)

        # TODO: Evaluate what to do with this
        # tbot.log.message("Testing formatting ...")
        # tmp = linux.Path(m, "/tmp/f o/bar")
        # out = m.exec0("echo", linux.F("{}:{}:{}", tmp, linux.Pipe, "foo"))
        # assert out == "/tmp/f o/bar:|:foo\n", repr(out)

        # TODO: Hm?
        # m.exec0("export", linux.F("NEWPATH={}:{}", tmp, linux.Env("PATH"), quote=False))
        # out = m.env("NEWPATH")
        # assert out != "/tmp/f o/bar:${PATH}", repr(out)

        if "jobs" in cap:
            t1 = time.monotonic()
            out = m.exec0(
                "sleep", "infinity", linux.Background, "echo", "Hello World"
            ).strip()
            t2 = time.monotonic()
            pid = m.env("!")

            tbot.log.message(pid)

            assert re.match(r"\[\d+\] \d+\nHello World", out), repr(out)
            assert (
                t2 - t1
            ) < 9.0, (
                f"Command took {t2 - t1}s (max 9s). Sleep was not sent to background"
            )

            # Kill the sleep process.  In some circumstances, tbot does not
            # seem to be able to kill all child processes of a subprocess
            # channel.  To prevent this from leading to issues, kill the sleep
            # right here instead of relying on tbot to do so correctly at the
            # very end.      Tracking-Issue: Rahix/tbot#13
            m.exec("kill", pid, linux.Then, "wait", pid)

            f1 = m.workdir / "bg1.txt"
            f2 = m.workdir / "bg2.txt"
            out = m.exec0(
                "echo",
                "foo",
                linux.Background(stdout=f1),
                "echo",
                "bar",
                linux.Background(stdout=f2, stderr=f2),
                "wait",
            )
            out = f1.read_text().strip()
            assert out == "foo", repr(out)
            out = f2.read_text().strip()
            assert out == "bar", repr(out)

        if "control" in cap:
            out = m.exec0(
                "false", linux.AndThen, "echo", "FOO", linux.OrElse, "echo", "BAR"
            ).strip()
            assert out == "BAR", repr(out)

            out = m.exec0(
                "true", linux.AndThen, "echo", "FOO", linux.OrElse, "echo", "BAR"
            ).strip()
            assert out == "FOO", repr(out)

        tbot.log.message("Testing subshell ...")
        out = m.env("SUBSHELL_TEST_VAR")
        assert out == "", repr(out)

        with m.subshell():
            out_b = m.env("SUBSHELL_TEST_VAR", "123")
            out = m.env("SUBSHELL_TEST_VAR")
            assert out == "123", repr(out)
            assert out_b == "123", repr(out_b)

        out = m.env("SUBSHELL_TEST_VAR")
        assert out == "", repr(out)

        if "run" in cap:
            tbot.log.message("Testing mach.run() ...")

            # Test simple uses where everything works as expected
            f = m.workdir / "test_run.txt"
            with m.run("cat", linux.RedirStdout(f)) as cat:
                cat.sendline("Hello World")
                cat.sendline("Lorem ipsum")

                cat.sendcontrol("D")
                cat.terminate0()

            with m.run("cat", f) as cat:
                content = cat.terminate0()

            assert content == "Hello World\nLorem ipsum\n", repr(content)

            with m.run("bash", "--norc", "--noprofile", "--noediting") as bs:
                bs.sendline("exit")
                bs.terminate0()

            # Test failing cases

            # Use after terminate
            with m.run("cat") as cat:
                cat.sendcontrol("D")
                cat.terminate0()

                raised = False
                try:
                    cat.sendline("Hello World")
                except linux.CommandEndedException:
                    raised = True
                assert raised, "Channel was not sealed after command exit."

                raised = False
                try:
                    cat.terminate0()
                except Exception:
                    raised = True
                assert raised, "Proxy did not complain about multiple terminations."

            # Unexpected abort
            with m.run("echo", "Hello World", linux.Then, "false") as echo:
                raised = False
                try:
                    echo.read_until_prompt("Lorem Ipsum")
                except linux.CommandEndedException:
                    raised = True
                assert raised, "Early abort of interactive command was not detected!"

                raised = False
                try:
                    echo.sendline("Hello World")
                except linux.CommandEndedException:
                    raised = True
                assert raised, "Channel was not sealed after command exit."

                retcode, _ = echo.terminate()
                assert retcode == 1, "Did not capture retcode of early exiting command"

            # Bad return code
            raised = False
            try:
                with m.run("false") as false:
                    false.terminate0()
            except Exception:
                raised = True

            assert raised, "Failing command was not detected properly!"

            with m.run("sh", "-c", "exit 123") as sh:
                rc = sh.terminate()[0]
                assert rc == 123, f"Expected return code 123, got {rc!r}"

            # Missing terminate
            raised = False
            try:
                with m.run("echo", "Hello World"):
                    pass
            except RuntimeError:
                raised = True
                # Necessary to bring machine back into good state
                m.ch.read_until_prompt()

            assert raised, "Missing terminate did not lead to error"

            m.exec0("true")

    if isinstance(m, board.UBootShell):
        tbot.log.message("Testing env vars ...")

        m.exec0("setenv", "TBOT_TEST", "Lorem ipsum dolor sit amet")
        out = m.exec0("printenv", "TBOT_TEST")
        assert out == "TBOT_TEST=Lorem ipsum dolor sit amet\n", repr(out)

        out = m.env("TBOT_TEST")
        assert out == "Lorem ipsum dolor sit amet", repr(out)


@tbot.testcase
def selftest_machine_channel(lab: typing.Optional[linux.Lab] = None,) -> None:
    with channel.SubprocessChannel() as ch:
        ch.read()
        # Test a simple command
        ch.sendline("echo Hello World", read_back=True)
        out = ch.read()
        assert out.startswith(b"Hello World"), repr(out)

    with channel.SubprocessChannel() as ch:
        ch.read()
        # Test reading
        ch.write(b"1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        out = ch.read(10)
        assert out == b"1234567890", repr(out)

        out = ch.read()
        assert out == b"ABCDEFGHIJKLMNOPQRSTUVWXYZ", repr(out)

    with channel.SubprocessChannel() as ch:
        ch.read()
        # Test read iter
        ch.write(b"12345678901234567890")
        final = bytearray()
        for new in ch.read_iter(10):
            final.extend(new)
        assert final == b"1234567890", repr(final)
        for i in range(1, 10):
            c = ch.read(1)
            assert c == str(i).encode("utf-8"), repr(c)

    with channel.SubprocessChannel() as ch:
        ch.read()
        # Test readline
        ch.sendline("echo Hello; echo World", read_back=True)
        out_s = ch.readline()
        assert out_s == "Hello\n", repr(out)
        out_s = ch.readline()
        assert out_s == "World\n", repr(out)

    # Test expect
    with channel.SubprocessChannel() as ch:
        ch.read()
        ch.sendline("echo Lorem Ipsum")
        res = ch.expect(["Lol", "Ip"])
        assert res.i == 1, repr(res)
        assert res.match == "Ip", repr(res)

    with channel.SubprocessChannel() as ch:
        ch.read()
        ch.sendline("echo Lorem Ipsum Dolor Sit")
        res = ch.expect(["Lol", "Dolor", "Dol"])
        assert res.i == 1, repr(res)
        assert res.match == "Dolor", repr(res)

    with channel.SubprocessChannel() as ch:
        ch.read()
        ch.sendline("echo Lo1337rem")
        res = ch.expect(["Dolor", "roloD", tbot.Re(r"Lo(\d{1,20})"), "rem"])
        assert res.i == 2, repr(res)
        assert isinstance(res.match, typing.Match), "Not a match object"
        assert res.match.group(1) == b"1337", repr(res)

    with channel.SubprocessChannel() as ch:
        # Test Borrow
        ch.sendline("echo Hello")

        with ch.borrow() as ch2:
            ch2.sendline("echo World")

            raised = False
            try:
                ch.sendline("echo Illegal")
            except channel.ChannelBorrowedException:
                raised = True

            assert raised, "Borrow was unsuccessful"

        ch.sendline("echo back again")

    with channel.SubprocessChannel() as ch:
        # Test Move
        ch.sendline("echo Hello")

        ch2 = ch.take()
        ch2.sendline("echo World")

        raised = False
        try:
            ch.sendline("echo Illegal")
        except channel.ChannelTakenException:
            raised = True

        assert raised, "Take was unsuccessful"
