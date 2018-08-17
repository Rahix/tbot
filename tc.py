import typing
import tbot
from tbot.machine import linux


@tbot.testcase
def uname(
    lh: typing.Optional[tbot.machine.linux.LinuxMachine] = None,
) -> None:
    with lh or tbot.acquire_lab() as lh:
        lh.exec0("uname", "-a")


@tbot.testcase
def stat(
    lh: typing.Optional[tbot.machine.linux.LinuxMachine] = None,
) -> None:
    with lh or tbot.acquire_lab() as lh:
        symlink = lh.workdir / "symlink"
        if symlink.exists():
            lh.exec0("rm", symlink)
        lh.exec0("ln", "-s", "/proc/version", symlink)

        fifo = lh.workdir / "fifo"
        if fifo.exists():
            lh.exec0("rm", fifo)
        lh.exec0("mkfifo", fifo)

        for p in [
            linux.Path(lh, "/dev"),
            linux.Path(lh, "/proc/version"),
            symlink,
            linux.Path(lh, "/dev/sda"),
            linux.Path(lh, "/dev/tty"),
            fifo,
        ]:
            tbot.log.message(f"{p}: {p.is_dir()} {p.is_file()} {p.is_symlink()} {p.is_block_device()} {p.is_char_device()} {p.is_fifo()} {p.is_socket()}")
