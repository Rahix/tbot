import typing
import tbot
from tbot.machine import channel
from tbot.machine import linux
from tbot.machine import board

__all__ = ["selftest_machine_reentrant", "selftest_machine_labhost_shell"]


@tbot.testcase
def selftest_machine_reentrant(lh: typing.Optional[linux.LabHost] = None,) -> None:
    with lh or tbot.acquire_lab() as lh:
        with lh as h1:
            assert h1.exec0("echo", "FooBar") == "FooBar\n"

        with lh as h2:
            assert h2.exec0("echo", "FooBar2") == "FooBar2\n"


@tbot.testcase
def selftest_machine_labhost_shell(lh: typing.Optional[linux.LabHost] = None,) -> None:
    with lh or tbot.acquire_lab() as lh:
        selftest_machine_shell(lh)

        selftest_machine_channel(lh.new_channel())


@tbot.testcase
def selftest_machine_shell(
    m: typing.Union[linux.LinuxMachine, board.UBootMachine]
) -> None:
    # Capabilities
    cap = []
    if isinstance(m, linux.LinuxMachine):
        if m.shell == "bash":
            cap.extend(["printf"])
        if m.shell in ["ash", "dash"]:
            cap.extend(["printf"])

    tbot.log.message("Testing command output ...")
    out = m.exec0("echo", "Hello World")
    assert out == "Hello World\n", repr(out)

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
    r, _ = m.exec("true")
    assert r == 0, repr(r)

    r, _ = m.exec("false")
    assert r == 1, repr(r)

    if isinstance(m, linux.LinuxMachine):
        tbot.log.message("Testing env vars ...")
        m.exec0("export", "TBOT_TEST_ENV_VAR=121212")
        out = m.exec0("echo", linux.Env("TBOT_TEST_ENV_VAR"))
        assert out == "121212\n", repr(out)

        tbot.log.message("Testing redirection ...")
        f = m.workdir / ".redir_test.txt"
        if f.exists():
            m.exec0("rm", f)

        m.exec0("echo", "Some data\nAnd some more", stdout=f)

        out = m.exec0("cat", f)
        assert out == "Some data\nAnd some more\n", repr(out)

    if isinstance(m, board.UBootMachine):
        tbot.log.message("Testing env vars ...")
        m.exec0("setenv", "TBOT_TEST", "Lorem ipsum dolor sit amet")
        out = m.exec0("printenv", "TBOT_TEST")
        assert out == "TBOT_TEST=Lorem ipsum dolor sit amet\n", repr(out)


@tbot.testcase
def selftest_machine_channel(ch: channel.Channel) -> None:
    out = ch.raw_command("echo Hello World")
    assert out == "Hello World\n", repr(out)

    ch.close()

    raised = False
    try:
        ch.send("\n")
    except channel.ChannelClosedException:
        raised = True
    assert raised

    raised = False
    try:
        ch.recv()
    except channel.ChannelClosedException:
        raised = True
    assert raised
