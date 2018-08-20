import typing
import stat
import tbot
from tbot import machine
from tbot.machine import linux


@tbot.testcase
def selftest_path_integrity(
    lh: typing.Optional[linux.LabHost] = None,
) -> None:
    with lh or tbot.acquire_lab() as lh:
        p = lh.workdir / "folder" / "file.txt"

        with tbot.acquire_lab() as lh2:
            raised = False
            try:
                # mypy detects that this is wrong
                lh2.exec0("echo", p)  # type: ignore
            except machine.WrongHostException:
                raised = True
            assert raised

        lh.exec0("mkdir", "-p", p.parent)
        assert p.parent.is_dir()
        lh.exec0("uname", "-a", stdout=p)
        assert p.is_file()
        lh.exec0("rm", "-r", p.parent)
        assert not p.exists()
        assert not p.parent.exists()


@tbot.testcase
def selftest_stat(
    lh: typing.Optional[linux.LabHost] = None,
) -> None:
    with lh or tbot.acquire_lab() as lh:
        tbot.log.message("Setting up test files ...")
        symlink = lh.workdir / "symlink"
        if symlink.exists():
            lh.exec0("rm", symlink)
        lh.exec0("ln", "-s", "/proc/version", symlink)

        fifo = lh.workdir / "fifo"
        if fifo.exists():
            lh.exec0("rm", fifo)
        lh.exec0("mkfifo", fifo)

        nonexistent = lh.workdir / "nonexistent"
        if nonexistent.exists():
            lh.exec0("rm", nonexistent)

        # Existence checks
        tbot.log.message("Checking existence ...")
        assert not (lh.workdir / "nonexistent").exists()
        assert symlink.exists()

        # File mode checks
        tbot.log.message("Checking file modes ...")
        assert linux.Path(lh, "/dev").is_dir()
        assert linux.Path(lh, "/proc/version").is_file()
        assert symlink.is_symlink()
        assert linux.Path(lh, "/dev/sda").is_block_device()
        assert linux.Path(lh, "/dev/tty").is_char_device()
        assert fifo.is_fifo()

        # File mode nonexistence checks
        tbot.log.message("Checking file modes on nonexistent files ...")
        assert not nonexistent.is_dir()
        assert not nonexistent.is_file()
        assert not nonexistent.is_symlink()
        assert not nonexistent.is_block_device()
        assert not nonexistent.is_char_device()
        assert not nonexistent.is_fifo()
        assert not nonexistent.is_socket()

        stat_list = [
            (linux.Path(lh, "/dev"), stat.S_ISDIR),
            (linux.Path(lh, "/proc/version"), stat.S_ISREG),
            (symlink, stat.S_ISLNK),
            (linux.Path(lh, "/dev/sda"), stat.S_ISBLK),
            (linux.Path(lh, "/dev/tty"), stat.S_ISCHR),
            (fifo, stat.S_ISFIFO),
        ]

        tbot.log.message("Checking stat results ...")
        for p, check in stat_list:
            assert check(p.stat().st_mode)
