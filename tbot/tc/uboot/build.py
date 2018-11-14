import contextlib
import typing
import tbot
from tbot.machine import linux
from tbot.tc import uboot

BH = typing.TypeVar("BH", bound=linux.BuildMachine)


@tbot.testcase
def build(
    build_machine: typing.Optional[BH] = None,
    build_info: typing.Optional[typing.Type[uboot.BuildInfo]] = None,
    clean: bool = True,
) -> linux.Path[BH]:
    """
    Build U-Boot.

    :param linux.BuildMachine build_machine: Machine where to build U-Boot
    :param uboot.BuildInfo build_info: Build parameters
    :rtype: linux.Path
    :returns: Path to the build dir
    """
    with contextlib.ExitStack() as cx:
        if build_machine is not None:
            bh: linux.BuildMachine = build_machine
        else:
            lh = cx.enter_context(tbot.acquire_lab())
            bh = cx.enter_context(lh.build())

        if build_info is not None:
            bi = build_info(bh)
        else:
            bi = getattr(tbot.selectable.UBootMachine, "build")(bh)

        repo = bi.checkout(clean)

        with bh if bi.toolchain is None else bh.enable(bi.toolchain):
            bh.exec0("cd", repo)
            if clean:
                bh.exec0("make", "mrproper")
                bh.exec0("make", bi.defconfig)

            nproc = bh.exec0("nproc", "--all").strip()
            bh.exec0("make", "-j", nproc, "all")

        return repo
