import tbot
from tbot.machine import linux

@tbot.testcase
def cat_file(f: linux.Path) -> str:
    return f.host.exec0("cat", f)


@tbot.testcase
def test_devel() -> None:
    from config.labs import dummy
    lh = dummy.DummyLab()

    v = cat_file(linux.Path(lh, "/proc/version"))
    print(f"Version: {v}")

    f = linux.Path(lh, lh.workdir / "myfile.txt")
    lh.exec0("uname", "-n", stdout=f)

    name = cat_file(f)
    print(f"Name: {name}")


if __name__ == "__main__":
    test_devel()
