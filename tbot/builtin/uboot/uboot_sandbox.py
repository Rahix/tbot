"""
Run U-Boot tests inside the sandbox
-----------------------------------
"""
import os
import tbot

@tbot.testcase
def uboot_sandbox(tb: tbot.TBot) -> None:
    """ Run U-Boot tests inside the sandbox """
    build_dir = os.path.join(
        tb.config.workdir,
        f"u-boot-sandbox")
    patchdir = tb.config.try_get("uboot.patchdir")

    tb.call("clean_repo_checkout",
            repo=tb.config.get("uboot.repository"),
            target=build_dir)
    if patchdir is not None:
        tb.call("apply_git_patches", gitdir=build_dir, patchdir=patchdir)

    tb.log.doc_log("""
## Run U-Boot tests inside sandbox on host (optional) ##
U-Boot contains a python test suite that can be run on the host and on the target.
Here we will run it on the host. Make sure all dependencies are met.  Refer to
<http://git.denx.de/?p=u-boot.git;a=blob;f=test/py/README.md> for a list.
""")

    if tb.config.get("uboot.test_use_venv", True):
        tb.log.doc_log("""Create a virtualenv and install pytest inside it:
""")

        # Setup python
        tb.shell.exec0(f"cd {build_dir}; virtualenv-2.7 venv", log_show_stdout=False)

        with tb.machine(tbot.machine.MachineLabEnv()) as tbn:
            tbn.shell.exec0(f"cd {build_dir}")
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
            tbn.shell.exec0(f"cd {build_dir}")
            tbn.shell.exec0(f"make mrproper", log_show_stdout=False)

            @tbn.call
            def run_tests_no_venv(tb: tbot.TBot) -> None: #pylint: disable=unused-variable
                """ Actual test run """
                tb.shell.exec0(f"./test/py/test.py --bd sandbox --build")
