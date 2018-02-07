"""
Run U-Boot tests on real hardware
---------------------------------
"""
import pathlib
import tbot

@tbot.testcase
def uboot_tests(tb: tbot.TBot) -> None:
    """ Run U-Boot tests on real hardware """
    build_dir = tb.config.workdir / f"u-boot-{tb.config.board_name}"


    tb.log.doc_log("""
## Run U-Boot tests ##
U-Boot contains a python test suite that can be run on the host and on the target. \
Here we will run it on the target. Make sure all dependencies are met.  Refer to \
<http://git.denx.de/?p=u-boot.git;a=blob;f=test/py/README.md> for a list.
""")

    config = tb.config.try_get("uboot.test_config")
    if config is not None:
        tb.log.doc_log("""To ensure that the testcases work properly, we need a \
configuration file for the testsuite. Copy the config file into `test/py` inside \
the U-Boot tree:
""")

        config = pathlib.PurePosixPath(config)
        filename = config.name
        target = build_dir / "test" / "py" / filename
        tb.shell.exec0(f"cp {config} {target}")

        tb.log.doc_log("The config file can be found in the appendix of this document.\n")
        cfg_file_content = tb.shell.exec0(f"cat {config}", log_show=False)
        tb.log.doc_appendix(f"U-Boot test config: {filename}", f"""```python
{cfg_file_content}
```""")

    if tb.config.get("uboot.test_use_venv", True):
        tb.log.doc_log("Create a virtualenv and install pytest inside it:\n")

        # Setup python
        tb.shell.exec0(f"cd {build_dir}; virtualenv-2.7 venv", log_show_stdout=False)

        with tb.machine(tbot.machine.MachineLabEnv()) as tbn:
            tbn.shell.exec0(f"cd {build_dir}")
            tbn.shell.exec0(f"VIRTUAL_ENV_DISABLE_PROMPT=1 source venv/bin/activate",
                            log_show_stdout=False)
            tbn.shell.exec0(f"pip install pytest", log_show_stdout=False)

            tbn.log.doc_log("Install the necessary hooks and start the U-Boot \
testsuite using the following commands:\n")
            tbn.shell.exec0(f"export PATH={tbn.config.get('uboot.test_hooks')}:$PATH")

            @tbn.call
            def run_tests(tb: tbot.TBot) -> None: #pylint: disable=unused-variable
                """ Actual test run """
                with tb.machine(tbot.machine.MachineBoardDummy(False)) as tbn:
                    tbn.shell.exec0(f"\
./test/py/test.py --bd {tb.config.get('uboot.test_boardname')}")

                    tb.log.doc_log("The U-Boot testsuite, which has hopefully finished \
successfully by now, is not capable of turning off the board itself. \
You have to do that manually:\n")

    else:
        tb.log.doc_log("""Here we do not use virtualenv because our build host \
does not have it installed, but it is recommended to do so. \
Install the necessary hooks and start the U-Boot testsuite using the following commands:
""")

        with tb.machine(tbot.machine.MachineLabEnv()) as tbn:
            tbn.shell.exec0(f"cd {build_dir}")
            tbn.shell.exec0(f"export PATH={tbn.config.get('uboot.test_hooks')}:$PATH")

            @tbn.call
            def run_tests_no_venv(tb: tbot.TBot) -> None: #pylint: disable=unused-variable
                """ Actual test run """
                with tb.machine(tbot.machine.MachineBoardDummy(False)) as tbn:
                    tbn.shell.exec0(f"\
./test/py/test.py --bd {tb.config.get('uboot.test_boardname')}")

                    tb.log.doc_log("The U-Boot testsuite, which has hopefully finished \
successfully by now, is not capable of turning off the board itself. \
You have to do that manually:\n")
