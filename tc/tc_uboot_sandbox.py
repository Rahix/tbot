""" Test uboot tests inside the sandbox """
import os
import tbot

@tbot.testcase
def tc_uboot_sandbox(tb):
    """ Test uboot tests inside the sandbox """
    if not tb.shell.shell_type[0] == "sh":
        raise "Need an sh shell"

    build_dir = os.path.join(
        tb.config.workdir,
        f"u-boot-{tb.config.board_name}")

    tb.log.doc_log("""
## Run uboot tests inside sandbox on host (optional) ##
Uboot contains a python test suite that can be run on the host and on the target.
Here we will run it on the host.  
Start by creating a virtualenv and installing pytest inside it:
""")

    # Setup python
    tb.shell.exec0(f"cd {build_dir}; virtualenv-2.7 venv", log_show_stdout=False)

    with tb.new_shell(tbot.shell.sh_env.ShellShEnv) as tbn:
        tbn.shell.exec0(f"cd {build_dir}")
        tbn.shell.exec0(f"VIRTUAL_ENV_DISABLE_PROMPT=1 source venv/bin/activate",
                        log_show_stdout=False)
        tbn.shell.exec0(f"pip install pytest", log_show_stdout=False)

        tbn.log.doc_log(f"""Now clean the uboot repository and start the sandbox testsuite.
""")
        tbn.shell.exec0(f"make mrproper", log_show_stdout=False)
        tbn.shell.exec0(f"./test/py/test.py --bd sandbox --build")
