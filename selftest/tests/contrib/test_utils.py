import contextlib
import typing
from typing import Callable, ContextManager, Iterator

import pytest
import testmachines

import tbot
import tbot_contrib.utils

if typing.TYPE_CHECKING:
    TestDir = Callable[[], ContextManager[tbot.machine.linux.Path]]


@pytest.fixture
def testdir_builder(tbot_context: tbot.Context) -> "TestDir":
    @contextlib.contextmanager
    def inner() -> Iterator[tbot.machine.linux.Path]:
        with tbot_context.request(testmachines.Localhost) as linux_shell:
            testdir = linux_shell.workdir / "utils-tests"
            linux_shell.exec0("rm", "-rf", testdir)
            linux_shell.exec0("mkdir", testdir)
            yield testdir

    return inner


def test_hashcmp(testdir_builder: "TestDir") -> None:
    with testdir_builder() as testdir:
        a = testdir / "file-a.txt"
        b = testdir / "file-b.txt"
        c = testdir / "file-c.txt"

        missing = testdir / "missing.txt"
        assert not missing.exists()

        a.write_text("Hello World!\n")
        b.write_text("Hello World!\n")
        c.write_text("Hello darkness...\n")

        assert tbot_contrib.utils.hashcmp(a, b)
        assert not tbot_contrib.utils.hashcmp(a, c)
        assert not tbot_contrib.utils.hashcmp(b, c)
        assert not tbot_contrib.utils.hashcmp(a, missing)


def test_strip_ansi_escapes_smoke() -> None:
    in_str = "\x1B[33mSome colored text!\x1B[0m"
    expected_str = "Some colored text!"

    out_str = tbot_contrib.utils.strip_ansi_escapes(in_str)

    assert out_str == expected_str


def test_find_ip_address(tbot_context: tbot.Context) -> None:
    with tbot_context.request(testmachines.Localhost) as lo:
        # Check whether it is able to find a "default" address
        tbot_contrib.utils.find_ip_address(lo)

        # Check whether find_ip_address() works with a local address
        addr = tbot_contrib.utils.find_ip_address(lo, "127.0.0.1")
        assert addr == "127.0.0.1"


def test_copy_to_dir_single(tbot_context: tbot.Context) -> None:
    with tbot_context.request(testmachines.Localhost) as lo:
        testdir = lo.workdir / "selftest-copy-dir1"
        lo.exec0("rm", "-rf", testdir)
        lo.exec0("mkdir", testdir)

        source = testdir / "file.txt"
        source.write_text("Hello and welcome to the copy_to_dir() test!\n")

        target = testdir / "target"
        lo.exec0("mkdir", target)

        dest = tbot_contrib.utils.copy_to_dir(source, target)

        assert dest == target / "file.txt"

        content = dest.read_text()
        assert content == "Hello and welcome to the copy_to_dir() test!\n"


def test_copy_to_dir_multi(tbot_context: tbot.Context) -> None:
    with tbot_context.request(testmachines.Localhost) as lo:
        testdir = lo.workdir / "selftest-copy-dir"
        lo.exec0("rm", "-rf", testdir)
        lo.exec0("mkdir", testdir)

        for i in range(1, 6):
            (testdir / f"file{i}.txt").write_text(f"File {i}\n")

        target = testdir / "target"
        lo.exec0("mkdir", target)

        # Use glob() to find the test-files so that function also gets some
        # more test coverage.
        target_files = tbot_contrib.utils.copy_to_dir(testdir.glob("*.txt"), target)

        for i in range(1, 6):
            file = target / f"file{i}.txt"
            assert file in target_files
            content = file.read_text()
            assert content == f"File {i}\n"
