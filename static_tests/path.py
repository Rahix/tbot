from tbot.machine.linux import path
from tbot.machine import linux
import machine


def annotated(p: path.Path[machine.DummyLinuxMach2]) -> str:
    return p.host.exec0("cat", p)


def invalid_path() -> None:
    mach = machine.DummyMach()
    # should fail!
    path.Path(mach, "/tmp")

    mach_lnx = machine.DummyLinuxMach()
    p2 = path.Path(mach_lnx, "/tmp")

    # should fail!
    annotated(p2)

    mach2 = machine.DummyLinuxMach2()

    p3 = path.Path(mach2, "/tmp")
    annotated(p3)

    # should fail!
    mach_lnx.exec0("cat", p3)

    # should fail!
    mach_lnx.exec0("echo", linux.RedirStdout(p3 / "file"))

    # should fail!
    mach2.exec0("echo", linux.RedirStderr(p2 / "file2"))
