import typing
import time
import re
import tbot
from tbot.machine import channel
from tbot.machine import linux
from tbot.machine import board

__all__ = (
    "selftest_machine_reentrant",
    "selftest_machine_labhost_shell",
    "selftest_machine_ssh_shell",
    "selftest_machine_sshlab_shell",
)


@tbot.testcase
def selftest_machine_reentrant(lab: typing.Optional[linux.LabHost] = None,) -> None:
    """Test if a machine can be entered multiple times."""
    with lab or tbot.acquire_lab() as lh:
        with lh as h1:
            assert h1.exec0("echo", "FooBar") == "FooBar\n"

        with lh as h2:
            assert h2.exec0("echo", "FooBar2") == "FooBar2\n"


@tbot.testcase
def selftest_machine_labhost_shell(lab: typing.Optional[linux.LabHost] = None,) -> None:
    """Test the LabHost's shell."""
    with lab or tbot.acquire_lab() as lh:
        selftest_machine_shell(lh)

        selftest_machine_channel(lh.new_channel(), False)
        selftest_machine_channel(lh.new_channel(), True)


@tbot.testcase
def selftest_machine_ssh_shell(lab: typing.Optional[linux.LabHost] = None,) -> None:
    """Test an SSH shell."""
    from tbot.tc.selftest import minisshd

    with lab or tbot.acquire_lab() as lh:
        if minisshd.check_minisshd(lh):
            with minisshd.minisshd(lh) as ssh:
                selftest_machine_shell(ssh)

                selftest_machine_channel(ssh._obtain_channel(), True)
        else:
            tbot.log.message(tbot.log.c("Skip").yellow.bold + " ssh tests.")


@tbot.testcase
def selftest_machine_sshlab_shell(lab: typing.Optional[linux.LabHost] = None,) -> None:
    """Test an SSH LabHost shell."""
    from tbot.tc.selftest import minisshd

    with lab or tbot.acquire_lab() as lh:
        if minisshd.check_minisshd(lh):
            with minisshd.minisshd(lh) as ssh:
                ssh.exec0("true")

                with minisshd.MiniSSHLabHost(ssh.port) as sl:
                    selftest_machine_shell(sl)
        else:
            tbot.log.message(tbot.log.c("Skip").yellow.bold + " ssh tests.")


@tbot.testcase
def selftest_machine_shell(
    m: typing.Union[linux.LinuxMachine, board.UBootMachine]
) -> None:
    # Capabilities
    cap = []
    if isinstance(m, linux.LinuxMachine):
        if m.shell == linux.shell.Bash:
            cap.extend(["printf", "jobs", "control"])
        if m.shell == linux.shell.Ash:
            cap.extend(["printf", "control"])

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

    if isinstance(m, linux.LinuxMachine):
        tbot.log.message("Testing env vars ...")
        value = "12\nfoo !? # true; exit\n"
        m.env("TBOT_TEST_ENV_VAR", value)
        out = m.env("TBOT_TEST_ENV_VAR")
        assert out == value, repr(out)

        tbot.log.message("Testing redirection (and weird paths) ...")
        f = m.workdir / ".redir test.txt"
        if f.exists():
            m.exec0("rm", f)

        m.exec0("echo", "Some data\nAnd some more", stdout=f)

        out = m.exec0("cat", f)
        assert out == "Some data\nAnd some more\n", repr(out)

        tbot.log.message("Testing formatting ...")
        tmp = linux.Path(m, "/tmp/f o/bar")
        out = m.exec0("echo", linux.F("{}:{}:{}", tmp, linux.Pipe, "foo"))
        assert out == "/tmp/f o/bar:|:foo\n", repr(out)

        m.exec0("export", linux.F("NEWPATH={}:{}", tmp, linux.Env("PATH"), quote=False))
        out = m.env("NEWPATH")
        assert out != "/tmp/f o/bar:${PATH}", repr(out)

        if "jobs" in cap:
            t1 = time.monotonic()
            out = m.exec0(
                "sleep", "10", linux.Background, "echo", "Hello World"
            ).strip()
            t2 = time.monotonic()

            assert re.match(r"\[\d+\] \d+\nHello World", out), repr(out)
            assert (
                t2 - t1
            ) < 9.0, (
                f"Command took {t2 - t1}s (max 9s). Sleep was not sent to background"
            )

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
            m.env("SUBSHELL_TEST_VAR", "123")
            out = m.env("SUBSHELL_TEST_VAR")
            assert out == "123", repr(out)

        out = m.env("SUBSHELL_TEST_VAR")
        assert out == "", repr(out)

        shell = m.shell
        with m.subshell("env", "SUBSHELL_TEST_VAR2=1337", *shell.command, shell=shell):
            out = m.env("SUBSHELL_TEST_VAR2")
            assert out == "1337", repr(out)

    if isinstance(m, board.UBootMachine):
        tbot.log.message("Testing env vars ...")
        m.exec0("setenv", "TBOT_TEST", "Lorem ipsum dolor sit amet")
        out = m.exec0("printenv", "TBOT_TEST")
        assert out == "TBOT_TEST=Lorem ipsum dolor sit amet\n", repr(out)

        out = m.env("TBOT_TEST")
        assert out == "Lorem ipsum dolor sit amet", repr(out)


@tbot.testcase
def selftest_machine_channel(ch: channel.Channel, remote_close: bool) -> None:
    out = ch.raw_command("echo Hello World", timeout=1)
    assert out == "Hello World\n", repr(out)

    # Check recv_n
    ch.send("echo Foo Bar\n")
    out2 = ch.recv_n(8, timeout=1.0)
    assert out2 == b"echo Foo", repr(out)
    ch.read_until_prompt(channel.TBOT_PROMPT)

    # Check timeout
    raised = False
    try:
        ch.send("echo Foo Bar")
        ch.read_until_prompt(channel.TBOT_PROMPT, timeout=0)
    except TimeoutError:
        raised = True
    assert raised
    ch.send("\n")
    ch.read_until_prompt(channel.TBOT_PROMPT)

    assert ch.isopen()

    if remote_close:
        ch.send("exit\n")
        time.sleep(0.1)
        ch.recv(timeout=1)

        raised = False
        try:
            ch.recv(timeout=1)
        except channel.ChannelClosedException:
            raised = True
        assert raised
    else:
        ch.close()

    assert not ch.isopen()

    raised = False
    try:
        ch.send("\n")
    except channel.ChannelClosedException:
        raised = True
    assert raised

    raised = False
    try:
        ch.recv(timeout=1)
    except channel.ChannelClosedException:
        raised = True
    assert raised
