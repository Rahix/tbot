"""
Run U-Boot tests on real hardware
---------------------------------
"""
import pathlib
import tbot

@tbot.testcase
def uboot_tests(tb: tbot.TBot) -> None:
    """ Run U-Boot tests on real hardware """
    build_dir = tb.config["uboot.builddir"]
    toolchain = tb.config["board.toolchain"]


    tb.log.doc_log("""
## Run U-Boot tests ##
U-Boot contains a python test suite that can be run on the host and on the target. \
Here we will run it on the target. Make sure all dependencies are met.  Refer to \
<http://git.denx.de/?p=u-boot.git;a=blob;f=test/py/README.md> for a list.
""")

    config = tb.config["uboot.test.config", None]
    if config is not None:
        tb.log.doc_log("""To ensure that the testcases work properly, we need a \
configuration file for the testsuite. Copy the config file into `test/py` inside \
the U-Boot tree:
""")

        tb.log.log_debug(f"Using '{config}' for the U-Boot test suite")
        config = pathlib.PurePosixPath(config)
        filename = config.name
        target = build_dir / "test" / "py" / filename
        tb.shell.exec0(f"cp {config} {target}")

        tb.log.doc_log("The config file can be found in the appendix of this document.\n")
        cfg_file_content = tb.shell.exec0(f"cat {config}", log_show=False)
        tb.log.doc_appendix(f"U-Boot test config: {filename}", f"""```python
{cfg_file_content}
```""")

    def run_tests(tb: tbot.TBot) -> None:
        assert tb.shell.unique_machine_name == "labhost-env", "Need an env shell!"

        tb.log.doc_log("""Clean the workdir because the U-Boot testsuite won't \
recompile if it is dirty.
""")

        tb.shell.exec0(f"make mrproper", log_show_stdout=False)

        tb.log.doc_log("Install the necessary hooks and start the \
testsuite using the following commands:\n")
        tb.shell.exec0(f"export PATH={tb.config['uboot.test.hooks']}:$PATH")

        with tb.machine(tbot.machine.MachineBoardDummy(False)) as tbn:
            tbn.shell.exec0(f"\
./test/py/test.py --bd {tb.config['uboot.test.boardname']} --build")

            tbn.log.doc_log("The U-Boot testsuite, which has hopefully finished \
successfully by now, is not capable of turning off the board itself. \
You have to do that manually:\n")

    has_venv = tb.config["uboot.test.use_venv", True]
    tb.log.log_debug(f"Virtualenv availability: {has_venv}")
    if has_venv:
        tb.log.doc_log("Create a virtualenv and install pytest inside it:\n")

        # Setup python
        tb.shell.exec0(f"cd {build_dir}; virtualenv-2.7 venv", log_show_stdout=False)

        tb.log.doc_log("""The testsuite will rebuild the U-Boot binary. For doing so, \
it needs the correct toolchain enabled.
""")

        @tb.call_then("toolchain_env", toolchain=toolchain)
        def setup_venv(tb: tbot.TBot) -> None: #pylint: disable=unused-variable
            """ Actual test run """
            tb.shell.exec0(f"cd {build_dir}")
            tb.shell.exec0(f"VIRTUAL_ENV_DISABLE_PROMPT=1 source venv/bin/activate",
                           log_show_stdout=False)
            tb.shell.exec0(f"pip install pytest", log_show_stdout=False)

            tb.call(run_tests)

    else:
        tb.log.doc_log("""Here we do not use virtualenv because our build host \
does not have it installed, but it is recommended to do so.
""")

        tb.log.doc_log("""The testsuite will rebuild the U-Boot binary. For doing so, \
it needs the correct toolchain enabled.
""")

        @tb.call_then("toolchain_env", toolchain=toolchain)
        def setup_no_venv(tb: tbot.TBot) -> None: #pylint: disable=unused-variable
            """ Actual test run """
            tb.shell.exec0(f"cd {build_dir}")

            tb.call(run_tests)
