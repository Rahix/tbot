# tbot, Embedded Automation Tool
# Copyright (C) 2019  Harald Seiler
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import typing
import stat
import tbot
from tbot.machine import linux
from tbot.tc import selftest

__all__ = ["selftest_path_integrity", "selftest_path_stat", "selftest_path_files"]


@tbot.testcase
def selftest_path_integrity(lab: typing.Optional[selftest.SelftestHost] = None) -> None:
    """Test if using a path on the wrong host fails."""

    with lab or selftest.SelftestHost() as lh:
        p = lh.workdir / "folder" / "file.txt"

        with tbot.acquire_lab() as lh2:
            raised = False
            try:
                # mypy detects that this is wrong
                lh2.exec0("echo", p)  # type: ignore
            # TODO: Proper exception type
            except:  # noqa: E722
                raised = True
            assert raised

        # It is ok to clone a machine and reuse the path
        with lh.clone() as lh3:
            lh3.exec0("echo", p)

        lh.exec0("mkdir", "-p", p.parent)
        assert p.parent.is_dir()
        lh.exec0("uname", "-a", linux.RedirStdout(p))
        assert p.is_file()
        lh.exec0("rm", "-r", p.parent)
        assert not p.exists()
        assert not p.parent.exists()


@tbot.testcase
def selftest_path_stat(lab: typing.Optional[selftest.SelftestHost] = None) -> None:
    """Test path stat utilities."""

    with lab or selftest.SelftestHost() as lh:
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

        # Block device
        block_list = (
            lh.exec0(
                *["find", "/dev", "-type", "b"],
                linux.Raw("2>/dev/null"),
                linux.OrElse,
                "true",
            )
            .strip()
            .split("\n")
        )
        block_dev = None
        if block_list != []:
            block_dev = linux.Path(lh, "/dev") / block_list[0]

        # Existence checks
        tbot.log.message("Checking existence ...")
        assert not (lh.workdir / "nonexistent").exists()
        assert symlink.exists()

        # File mode checks
        tbot.log.message("Checking file modes ...")
        assert linux.Path(lh, "/dev").is_dir()
        assert linux.Path(lh, "/proc/version").is_file()
        assert symlink.is_symlink()
        if block_dev is not None:
            assert linux.Path(lh, block_dev).is_block_device()
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
            (linux.Path(lh, "/dev/tty"), stat.S_ISCHR),
            (fifo, stat.S_ISFIFO),
        ]

        if block_dev is not None:
            stat_list.insert(3, (linux.Path(lh, block_dev), stat.S_ISBLK))

        tbot.log.message("Checking stat results ...")
        for p, check in stat_list:
            assert check(p.stat().st_mode)


@tbot.testcase
def selftest_path_files(lab: typing.Optional[selftest.SelftestHost] = None) -> None:
    """Test accessing file via the Path class"""

    with lab or selftest.SelftestHost() as lh:
        f = lh.workdir / "test-file.dat"

        tbot.log.message("Testing text file access ...")
        content = "This is a test file\nwith multiple lines.\n"

        f.write_text(content)
        output = f.read_text()

        assert output == content, f"Sending {content!r} resulted in {output!r}"

        tbot.log.message("Testing binary file access ...")
        content_bin = b"\x00\x1b[m\x04\x01\x10"

        assert f.write_bytes(content_bin) == len(content_bin), "Length mismatch"
        output_bin = f.read_bytes()

        assert (
            output_bin == content_bin
        ), f"Sending {content_bin!r} resulted in {output_bin!r}"

        tbot.log.message("Test reading/writing invalid file ...")
        f = lh.workdir / "path-test.50278c53-3cfc-4983-9770-d571b29b3955"

        # Writing/reading a directory should always fail
        lh.exec0("mkdir", "-p", f)

        raised = False
        try:
            f.write_text("Hello World\n")
        except Exception:
            raised = True

        assert raised, "Writing invalid file supposedly succeeded (text mode)"

        raised = False
        try:
            f.read_text()
        except Exception:
            raised = True

        assert raised, "Reading invalid file supposedly succeeded (text mode)"

        raised = False
        try:
            f.write_bytes(b"Hello World\n")
        except Exception:
            raised = True

        assert raised, "Writing invalid file supposedly succeeded (binary mode)"

        raised = False
        try:
            f.read_bytes()
        except Exception:
            raised = True

        assert raised, "Reading invalid file supposedly succeeded (binary mode)"
