import contextlib
import typing
from typing import Callable, ContextManager, Iterator, Optional

import pytest
import tbot
import testmachines
from conftest import AnyLinuxShell
from tbot.machine import linux

if typing.TYPE_CHECKING:
    TestDir = Callable[[], ContextManager[tbot.machine.linux.Path]]


@pytest.fixture
def testdir_builder(any_linux_shell: AnyLinuxShell) -> "TestDir":
    @contextlib.contextmanager
    def inner() -> Iterator[tbot.machine.linux.Path]:
        with any_linux_shell() as linux_shell:
            testdir = linux_shell.workdir / "path-tests"
            linux_shell.exec0("rm", "-rf", testdir)
            linux_shell.exec0("mkdir", testdir)
            yield testdir

    return inner


def get_blockdev(host: linux.LinuxShell) -> Optional[linux.Path]:
    blockdevices = host.exec(
        "find", "/dev", "-type", "b", linux.RedirStderr(host.fsroot / "dev" / "null")
    )[1].splitlines()
    if blockdevices == []:
        return None
    blockdev = linux.Path(host, blockdevices[0])
    assert blockdev.is_block_device()
    return blockdev


def test_purepath(tbot_context: tbot.Context) -> None:
    with tbot_context.request(testmachines.Localhost) as lo:
        p = lo.workdir / "foo" / "bar" / "baz"

        assert p.parent.name == "bar"
        assert p.parents[0].name == "bar"
        assert p.parents[1].name == "foo"
        assert p.parents[2] == lo.workdir


def test_integrity(tbot_context: tbot.Context) -> None:
    with tbot_context.request(testmachines.Localhost) as lo:
        p = lo.workdir / "abcdef"

        with testmachines.Localhost() as lo2:
            with pytest.raises(tbot.error.WrongHostError):
                # MYPY knows this is wrong :)
                lo2.exec0("echo", p)  # type: ignore

        with lo.clone() as lo3:
            lo3.exec0("echo", p)


def test_missing(testdir_builder: "TestDir") -> None:
    with testdir_builder() as testdir:
        missing = testdir / "a-file-that-does-not-exist"
        assert not missing.exists()

        assert not missing.is_dir()
        assert not missing.is_file()
        assert not missing.is_symlink()
        assert not missing.is_block_device()
        assert not missing.is_char_device()
        assert not missing.is_fifo()
        assert not missing.is_socket()

        with pytest.raises(NotADirectoryError):
            missing.rmdir()

        with pytest.raises(FileNotFoundError):
            missing.unlink()

        missing.unlink(missing_ok=True)

        missing.mkdir()
        assert missing.exists()
        assert missing.is_dir()


def test_regular_file(testdir_builder: "TestDir") -> None:
    with testdir_builder() as testdir:
        regular_file = testdir / "a-regular-file"
        testdir.host.exec0("touch", regular_file)
        assert regular_file.exists()
        assert regular_file.is_file()
        assert not regular_file.is_dir()
        assert not regular_file.is_symlink()
        assert not regular_file.is_block_device()
        assert not regular_file.is_char_device()
        assert not regular_file.is_fifo()
        assert not regular_file.is_socket()

        with pytest.raises(NotADirectoryError):
            regular_file.rmdir()

        with pytest.raises(FileExistsError):
            regular_file.mkdir()

        with pytest.raises(FileExistsError):
            # exception is still raised as path is not a directory
            regular_file.mkdir(exist_ok=True)

        regular_file.unlink()

        assert not regular_file.exists()
        assert not regular_file.is_file()


def test_directory(testdir_builder: "TestDir") -> None:
    with testdir_builder() as testdir:
        directory = testdir / "directory"
        testdir.host.exec0("mkdir", directory)
        assert directory.exists()
        assert directory.is_dir()
        assert not directory.is_file()
        assert not directory.is_symlink()

        with pytest.raises(Exception):
            directory.unlink()

        assert directory.exists()
        assert directory.is_dir()

        with pytest.raises(FileExistsError):
            directory.mkdir()

        directory.mkdir(exist_ok=True)

        directory.rmdir()

        assert not directory.exists()
        assert not directory.is_dir()


def test_blockdev(any_linux_shell: AnyLinuxShell) -> None:
    with any_linux_shell() as linux_shell:
        blockdev = get_blockdev(linux_shell)
        if blockdev is None:
            pytest.skip(f"Could not find any blockdevices on this host")
        assert blockdev.is_block_device()

        assert not blockdev.is_dir()
        assert not blockdev.is_file()
        assert not blockdev.is_symlink()
        assert not blockdev.is_char_device()
        assert not blockdev.is_fifo()
        assert not blockdev.is_socket()


def test_symlink(testdir_builder: "TestDir") -> None:
    with testdir_builder() as testdir:
        target = testdir / "symlink-target"
        symlink = testdir / "symlink"
        testdir.host.exec0("ln", "-s", target, symlink)

        # Deadlink right now
        assert symlink.is_symlink()
        assert not symlink.exists()
        assert not symlink.is_file()

        # Create the target
        testdir.host.exec0("touch", target)
        assert symlink.is_symlink()
        assert symlink.exists()
        assert symlink.is_file()
        assert not symlink.is_dir()

        with pytest.raises(NotADirectoryError):
            symlink.rmdir()

        with pytest.raises(FileExistsError):
            symlink.mkdir()

        with pytest.raises(FileExistsError):
            # exception is still raised as path is not a directory
            symlink.mkdir(exist_ok=True)

        symlink.unlink()

        assert not symlink.exists()
        assert not symlink.is_symlink()
        assert target.exists()

        target.unlink()
        target.mkdir()
        testdir.host.exec0("ln", "-s", target, symlink)
        assert symlink.is_symlink()
        assert symlink.exists()
        assert symlink.is_dir()
        assert not symlink.is_file()


def test_fifo(testdir_builder: "TestDir") -> None:
    with testdir_builder() as testdir:
        fifo = testdir / "fifo"
        testdir.host.exec0("mkfifo", fifo)
        assert fifo.exists()
        assert fifo.is_fifo()


def test_stat(any_linux_shell: AnyLinuxShell) -> None:
    import stat

    with any_linux_shell() as linux_shell:
        stat_list = [
            (linux.Path(linux_shell, "/dev"), stat.S_ISDIR),
            (linux.Path(linux_shell, "/proc/version"), stat.S_ISREG),
            (linux.Path(linux_shell, "/dev/tty"), stat.S_ISCHR),
        ]

        blockdev = get_blockdev(linux_shell)
        if blockdev is not None:
            stat_list.insert(3, (blockdev, stat.S_ISBLK))

        for p, check in stat_list:
            assert check(p.stat().st_mode)


def test_text_io(testdir_builder: "TestDir") -> None:
    with testdir_builder() as testdir:
        f = testdir / "test-file.txt"
        content = "This is a test file\nwith multiple lines.\n"

        f.write_text(content)
        output = f.read_text()

        assert output == content


def test_binary_io(testdir_builder: "TestDir") -> None:
    with testdir_builder() as testdir:
        f = testdir / "test-file.bin"
        content = b"\x00\x1b[m\x04\x01\x10"

        f.write_bytes(content)
        output = f.read_bytes()

        assert output == content


def test_write_dir_text(testdir_builder: "TestDir") -> None:
    with testdir_builder() as testdir:
        path = testdir / "test-dir"
        testdir.host.exec0("mkdir", "-p", path)

        with pytest.raises(Exception):
            path.write_text("Hello World\n")

        with pytest.raises(Exception):
            path.read_text()


def test_write_dir_binary(testdir_builder: "TestDir") -> None:
    with testdir_builder() as testdir:
        path = testdir / "test-dir"
        testdir.host.exec0("mkdir", "-p", path)

        with pytest.raises(Exception):
            path.write_bytes(b"\x01\x02")

        with pytest.raises(Exception):
            path.read_bytes()


def test_rmdir_nonempty(testdir_builder: "TestDir") -> None:
    with testdir_builder() as testdir:
        path = testdir / "test-dir"
        subdir = path / "subdir"

        testdir.host.exec0("mkdir", "-p", subdir)

        assert path.exists()
        assert path.is_dir()
        assert subdir.exists()
        assert subdir.is_dir()

        with pytest.raises(Exception):
            path.rmdir()


def test_mkdir_missing_parent(testdir_builder: "TestDir") -> None:
    with testdir_builder() as testdir:
        path = testdir / "missing" / "parent"

        with pytest.raises(FileNotFoundError):
            path.mkdir()

        with pytest.raises(FileNotFoundError):
            path.mkdir(exist_ok=True)

        path.mkdir(parents=True)

        with pytest.raises(FileExistsError):
            path.mkdir(parents=True)

        path.mkdir(parents=True, exist_ok=True)
