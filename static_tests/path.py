from tbot.machine.linux import path
import machine

def annotated(p: path.Path[machine.DummyLinuxMach2]) -> str:
    return p.host.exec0("cat", p)

def invalid_path() -> None:
    mach = machine.DummyMach()
    # should fail!
    p = path.Path(mach, "/tmp")

    mach_lnx = machine.DummyLinuxMach()
    p2 = path.Path(mach_lnx, "/tmp")

    # should fail!
    annotated(p2)

    mach2 = machine.DummyLinuxMach2()

    p3 = path.Path(mach2, "/tmp")
    annotated(p3)

    # should fail!
    mach_lnx.exec0("cat", p3)
