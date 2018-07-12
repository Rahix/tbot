"""
Demonstration of a git bisect
"""
import tbot


@tbot.testcase
def demo_bisect(tb: tbot.TBot) -> None:
    """ Demonstrate git bisecting """
    repo = tb.config["tbot.workdir"] / "uboot-bisect-demo"
    ubootdir = tb.call("uboot_checkout", clean=True, builddir=repo)
    toolchain = tb.call("toolchain_get")

    with tb.machine(tbot.machine.MachineBuild()) as tb:
        # Add 4 bad commits
        for i in range(0, 4):
            tbot.log.debug(f"({i+1}/4) Adding a bad commit ...")
            tb.shell.exec0(f"cd {repo}; echo 'asdfghjkl{i}' >>common/autoboot.c")

            string = "very ".join(map(lambda x: "", range(0, i + 1)))
            tb.shell.exec0(f"cd {repo}; git add common/autoboot.c")
            tb.shell.exec0(f"cd {repo}; git commit -m 'A {string}bad commit'")

        bad = tb.call(
            "git_bisect",
            gitdir=ubootdir,
            good="HEAD~20",
            and_then="uboot_build",
            params={"builddir": ubootdir, "toolchain": toolchain},
        )

        bad_commit = tb.shell.exec0(f"cd {repo}; git show {bad}")

    tbot.log.message(f"BAD COMMIT:\n{bad_commit}")
