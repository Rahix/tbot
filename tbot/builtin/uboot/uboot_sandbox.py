"""
Run U-Boot tests inside the sandbox
-----------------------------------
"""
import typing
import pathlib
import tbot

@tbot.testcase
@tbot.cmdline
def uboot_sandbox(tb: tbot.TBot, *,
                  repo: typing.Optional[str] = None,
                  builddir: typing.Optional[pathlib.PurePosixPath] = None,
                  patchdir: typing.Optional[pathlib.PurePosixPath] = None,
                 ) -> None:
    """
    Run U-Boot tests inside the sandbox

    :param repo: URI of the U-Boot repository, defaults to
                 ``tb.config["uboot.repository"]``
    :type repo: str
    :param builddir: Where to build U-Boot, defaults to
                     ``tb.config["tbot.workdir"] / "uboot-sandbox"``
    :type builddir: pathlib.PurePosixPath
    :param patchdir: Optional directory of patches to be applied. If this
                     parameter is not given, ``tb.config["uboot.patchdir"]``
                     will be used (If this is also empty, no patches will be
                     applied). Supply a nonexistent directory to force building
                     without patches.
    :type patchdir: pathlib.PurePosixPath
    """
    builddir = builddir or tb.config["tbot.workdir"] / "uboot-sandbox"
    patchdir = patchdir or tb.config["uboot.patchdir", None]

    tb.log.doc_log("""
## Run U-Boot tests inside sandbox on host (optional) ##

### U-Boot checkout for the sandbox ###
""")

    tb.call("uboot_checkout",
            repo=repo or tb.config["uboot.repository"],
            builddir=builddir,
            patchdir=patchdir)

    tb.log.doc_log("""
### Run sandbox tests ###
U-Boot contains a python test suite that can be run on the host and on the target.
Here we will run it on the host. Make sure all dependencies are met.  Refer to
<http://git.denx.de/?p=u-boot.git;a=blob;f=test/py/README.md> for a list.
""")

    if tb.config["uboot.test.use_venv", True]:
        tb.log.doc_log("""Create a virtualenv and install pytest inside it:
""")

        # Setup python
        tb.shell.exec0(f"cd {builddir}; virtualenv-2.7 venv", log_show_stdout=False)

        with tb.machine(tbot.machine.MachineLabEnv()) as tbn:
            tbn.shell.exec0(f"cd {builddir}")
            tbn.shell.exec0(f"VIRTUAL_ENV_DISABLE_PROMPT=1 source venv/bin/activate",
                            log_show_stdout=False)
            tbn.shell.exec0(f"pip install pytest", log_show_stdout=False)

            tbn.log.doc_log(f"""Now clean the U-Boot repository and start the sandbox testsuite.
""")
            tbn.shell.exec0(f"make mrproper", log_show_stdout=False)

            @tbn.call
            def run_tests(tb: tbot.TBot) -> None: #pylint: disable=unused-variable
                """ Actual test run """
                tb.shell.exec0(f"./test/py/test.py --bd sandbox --build")
    else:
        tb.log.doc_log("""Here we do not use virtualenv because our build host
does not have it installed, but it is recommended to do so.  
Clean the U-Boot repository and start the sandbox testsuite:
""")

        with tb.machine(tbot.machine.MachineLabEnv()) as tbn:
            tbn.shell.exec0(f"cd {builddir}")
            tbn.shell.exec0(f"make mrproper", log_show_stdout=False)

            @tbn.call
            def run_tests_no_venv(tb: tbot.TBot) -> None: #pylint: disable=unused-variable
                """ Actual test run """
                tb.shell.exec0(f"./test/py/test.py --bd sandbox --build")
