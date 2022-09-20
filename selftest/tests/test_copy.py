import pytest
import testmachines
from conftest import AnyLinuxShell

import tbot
from tbot.machine import linux


def test_local_copy(any_linux_shell: AnyLinuxShell) -> None:
    h: linux.LinuxShell
    with any_linux_shell() as h:
        testdir = h.workdir / "copy-tests"
        h.exec0("rm", "-rf", testdir)
        h.exec0("mkdir", testdir)

        src = testdir / "source.txt"
        dest = testdir / "destination.txt"

        src.write_text("Hello linux.copy()!\n")
        linux.copy(src, dest)

        content = dest.read_text()
        assert content == "Hello linux.copy()!\n"


@pytest.mark.parametrize("direction", ["to", "from"])  # type: ignore
def test_ssh_copy(direction: str, tbot_context: tbot.Context) -> None:
    with tbot_context() as cx:
        ssh = cx.request(testmachines.MocksshClient)
        if not ssh.has_sftp:
            pytest.skip("SFTP missing on server.")
        testdir_ssh = ssh.workdir / "ssh-copy-tests2"
        ssh.exec0("rm", "-rf", testdir_ssh)
        ssh.exec0("mkdir", testdir_ssh)
        file_ssh = testdir_ssh / "file.txt"

        lo = cx.request(testmachines.Localhost)
        testdir_lo = lo.workdir / "ssh-copy-tests1"
        lo.exec0("rm", "-rf", testdir_lo)
        lo.exec0("mkdir", testdir_lo)
        file_lo = testdir_lo / "file.txt"

        if direction == "to":
            src, dest = file_lo, file_ssh
        elif direction == "from":
            src, dest = file_ssh, file_lo
        else:
            raise Exception(f"unknown direction {direction!r}")

        expected = "Moin\n\nThis is a remote copy test!\n"
        src.write_text(expected)
        linux.copy(src, dest)
        content = dest.read_text()
        assert content == expected
