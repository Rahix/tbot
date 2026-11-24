import pathlib
import subprocess
import sys

import tbot
import tbot.newbot  # noqa: F401


def test_flags_are_set_for_completion(tmp_path: pathlib.Path) -> None:
    # a testcase module may decide with flags which testcases it has
    (tmp_path / "flagtcs.py").write_text(
        "import tbot\n\n"
        'if "myflag" in tbot.flags:\n\n'
        "    def flagged_tc() -> None:\n"
        "        pass\n"
    )
    res = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys, tbot.newbot; tbot.newbot.main(sys.argv[1:])",
            "-C",
            str(tmp_path),
            "-f",
            "myflag",
            "--complete-testcase",
            "flagtcs.f",
        ],
        capture_output=True,
        text=True,
        cwd=pathlib.Path(__file__).parents[2],
    )
    assert "flagtcs.flagged_tc" in res.stdout.split(), res.stdout + res.stderr
