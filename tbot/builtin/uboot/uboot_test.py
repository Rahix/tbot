""" Run U-Boot tests on real hardware """
import os
import tbot

@tbot.testcase
def uboot_tests(tb):
    """ Run U-Boot tests on real hardware """
    assert tb.shell.shell_type[0] == "sh", "Need an sh shell"

    build_dir = os.path.join(
        tb.config.workdir,
        f"u-boot-{tb.config.board_name}")


    power_cmd_off = tb.config.get("board.power.off_command")

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

        filename = os.path.basename(config)
        target = os.path.join(build_dir, "test", "py", filename)
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

        with tb.new_shell(tbot.shell.sh_env.ShellShEnv) as tbn:
            tbn.shell.exec0(f"cd {build_dir}")
            tbn.shell.exec0(f"VIRTUAL_ENV_DISABLE_PROMPT=1 source venv/bin/activate",
                            log_show_stdout=False)
            tbn.shell.exec0(f"pip install pytest", log_show_stdout=False)

            tbn.log.doc_log("Install the necessary hooks and start the U-Boot \
testsuite using the following commands:\n")
            tbn.shell.exec0(f"export PATH={tbn.config.get('uboot.test_hooks')}:$PATH")

            @tbn.call
            def run_tests(tb): #pylint: disable=unused-variable
                """ Actual test run """
                tb.shell.exec0(f"./test/py/test.py --bd {tb.config.get('uboot.test_boardname')}")

    else:
        tb.log.doc_log("""Here we do not use virtualenv because our build host \
does not have it installed, but it is recommended to do so. \
Install the necessary hooks and start the U-Boot testsuite using the following commands:
""")

        with tb.new_shell(tbot.shell.sh_env.ShellShEnv) as tbn:
            tbn.shell.exec0(f"cd {build_dir}")
            tbn.shell.exec0(f"export PATH={tbn.config.get('uboot.test_hooks')}:$PATH")

            @tbn.call
            def run_tests(tb): #pylint: disable=unused-variable
                """ Actual test run """
                tb.shell.exec0(f"./test/py/test.py --bd {tb.config.get('uboot.test_boardname')}")

    # Ensure the board is powered off
    tb.log.doc_log("The U-Boot testsuite, which has hopefully finished successfully by now, is \
not capable of turning off the board itself. You have to do that manually:\n")

    tb.shell.exec0(power_cmd_off, log_show_stdout=False)
