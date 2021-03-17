import tempfile

import pytest

try:
    from mypy import api as mypy_api
except ImportError:
    pytest.skip("mypy is missing", allow_module_level=True)


def do_static_test(source: str, expected: str) -> None:
    with tempfile.NamedTemporaryFile(suffix=".py") as f:
        f.write(source.encode())
        f.flush()
        stdout, stderr, retcode = mypy_api.run(["--no-incremental", f.name])
        assert stderr == ""
        assert retcode == 1
        messages = stdout.replace(f.name, "##FILE##")
        assert messages == expected


def test_path_mixing() -> None:
    do_static_test(
        """\
import tbot
from tbot.machine import linux


def annotated(p: linux.Path[tbot.role.BoardLinux]) -> str:
    return p.host.exec0("cat", p)


def invalid_path() -> None:
    with tbot.ctx() as cx:
        mach2 = cx.request(tbot.role.LocalHost)
        p2 = linux.Path(mach2, "/tmp")

        # should fail because p2 is for a wrong machine
        annotated(p2)

        mach3 = cx.request(tbot.role.BoardLinux)

        p3 = linux.Path(mach3, "/tmp")
        annotated(p3)

        # should fail because p3 is for mach3
        mach2.exec0("cat", p3)

        # should fail because p3 is for mach3
        mach2.exec0("echo", linux.RedirStdout(p3 / "file"))

        # should fail because p2 is for mach2
        mach3.exec0("echo", linux.RedirStderr(p2 / "file2"))
""",
        """\
##FILE##:15: error: Argument 1 to "annotated" has incompatible type "Path[LocalHost]"; expected "Path[BoardLinux]"
##FILE##:23: error: Argument 2 to "exec0" of "LinuxShell" has incompatible type "Path[BoardLinux]"; expected "Union[str, Special[LocalHost], Path[LocalHost]]"
##FILE##:26: error: Argument 1 to "RedirStdout" has incompatible type "Path[BoardLinux]"; expected "Path[LocalHost]"
##FILE##:29: error: Argument 1 to "RedirStderr" has incompatible type "Path[LocalHost]"; expected "Path[BoardLinux]"
Found 4 errors in 1 file (checked 1 source file)
""",
    )


def test_path_mixing2() -> None:
    do_static_test(
        """\
import tbot

def linux() -> None:
    with tbot.ctx() as cx:
        lo = cx.request(tbot.role.LocalHost)
        path_lo = lo.workdir / "foo"
        lh = cx.request(tbot.role.LabHost)
        path_lh = lh.workdir / "bar"
        lnx = cx.request(tbot.role.BoardLinux)
        path_lnx = lnx.workdir / "baz"

        # right
        lo.exec0("echo", path_lo)
        lh.exec0("echo", path_lh)
        lnx.exec0("echo", path_lnx)

        # wrong
        lo.exec0("echo", path_lh)
        lo.exec0("echo", path_lnx)
        lh.exec0("echo", path_lo)
        lh.exec0("echo", path_lnx)
        lnx.exec0("echo", path_lo)
        lnx.exec0("echo", path_lh)
""",
        """\
##FILE##:18: error: Argument 2 to "exec0" of "LinuxShell" has incompatible type "Path[LabHost]"; expected "Union[str, Special[LocalHost], Path[LocalHost]]"
##FILE##:19: error: Argument 2 to "exec0" of "LinuxShell" has incompatible type "Path[BoardLinux]"; expected "Union[str, Special[LocalHost], Path[LocalHost]]"
##FILE##:20: error: Argument 2 to "exec0" of "LinuxShell" has incompatible type "Path[LocalHost]"; expected "Union[str, Special[LabHost], Path[LabHost]]"
##FILE##:21: error: Argument 2 to "exec0" of "LinuxShell" has incompatible type "Path[BoardLinux]"; expected "Union[str, Special[LabHost], Path[LabHost]]"
##FILE##:22: error: Argument 2 to "exec0" of "LinuxShell" has incompatible type "Path[LocalHost]"; expected "Union[str, Special[BoardLinux], Path[BoardLinux]]"
##FILE##:23: error: Argument 2 to "exec0" of "LinuxShell" has incompatible type "Path[LabHost]"; expected "Union[str, Special[BoardLinux], Path[BoardLinux]]"
Found 6 errors in 1 file (checked 1 source file)
""",
    )
