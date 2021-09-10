import contextlib
import typing
from typing import Callable, ContextManager, Iterator

import pytest
from conftest import AnyLinuxShell

import tbot
import tbot_contrib.utils

if typing.TYPE_CHECKING:
    TestDir = Callable[[], ContextManager[tbot.machine.linux.Path]]


@pytest.fixture
def testdir_builder(any_linux_shell: AnyLinuxShell) -> "TestDir":
    @contextlib.contextmanager
    def inner() -> Iterator[tbot.machine.linux.Path]:
        with any_linux_shell() as linux_shell:
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
