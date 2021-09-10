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
