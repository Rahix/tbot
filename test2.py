import typing
import tbot
from tbot.machine import linux


@tbot.testcase
def foo_bar() -> None:
    with tbot.acquire_lab() as lh:
        lh.exec0("lsb_release", "-a")


@tbot.testcase
def test_imports() -> None:
    with tbot.acquire_lab() as lh:
        path = linux.Path(lh, "/tmp")

        lh.exec0("ls", path)
        lh.exec0("readlink", "-f", lh.workdir)

        with tbot.acquire_board(lh) as bd:
            with tbot.acquire_uboot(bd) as ub:
                ub.tmp_cmd("version")
                tbot.log.message(f"{ub!r}")


@tbot.testcase
def reentrant() -> None:
    tbot.log.message("Calling clean ...")
    reentrant_pattern()

    tbot.log.message("Calling nested ...")
    with tbot.acquire_lab() as lh:
        reentrant_pattern(lh)


@tbot.testcase
def reentrant_pattern(
    lh: typing.Optional[linux.LabHost] = None,
) -> None:
    with lh or tbot.acquire_lab() as lh:
        lh.exec0("lsb_release", "-a")


@tbot.testcase
def ssh_machine(
    lh: typing.Optional[linux.LabHost] = None,
) -> None:
    class MySSHMachine(linux.SSHMachine):
        name = "hercules-ssh"
        username = "hws"
        hostname = "hercules"

        @property
        def workdir(self) -> "linux.Path[MySSHMachine]":
            return linux.Path(self, "/tmp")

    with lh or tbot.acquire_lab() as lh:
        with MySSHMachine(lh) as ssh:
            ssh.exec0("uname", "-a")

            tbot.log.message(repr(ssh))


@tbot.testcase
def testsuite(
    *args: typing.Callable,
) -> None:
    errors: typing.List[Exception] = []

    for test in args:
        try:
            test()
        except Exception as e:
            errors.append(e)

    if errors != []:
        raise Exception(f"{len(errors)}/{len(args)} tests failed")


@tbot.testcase
def a() -> None:
    pass


@tbot.testcase
def b() -> None:
    pass


@tbot.testcase
def c() -> None:
    raise Exception("Error")


@tbot.testcase
def d() -> None:
    pass


@tbot.testcase
def e() -> None:
    raise Exception("Again :(")


@tbot.testcase
def f() -> None:
    pass


@tbot.testcase
def g() -> None:
    pass


@tbot.testcase
def h() -> None:
    raise RuntimeError("Error")


@tbot.testcase
def abc() -> None:
    """
    Run abc testsuite
    """
    testsuite(
        a,
        b,
        c,
        d,
        e,
        f,
        g,
        h,
    )


if __name__ == "__main__":
    test_imports()
