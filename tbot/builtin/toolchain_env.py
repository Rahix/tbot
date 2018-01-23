"""
Testcase to setup a toolchain environment
-----------------------------------------
"""
import tbot.shell.sh_env


@tbot.testcase
def toolchain_env(tb, toolchain=None, and_then=None, params=None):
    """
    Setup a toolchain environment and call a testcase inside

    :param toolchain: Which toolchain to use (str)
    :param and_then: What testcase to call inside the env (str)
    :param params: Parameters for the testcase (dict)
    """
    assert tb.shell.shell_type[0] == "sh", "Need an sh shell"

    if params is None:
        params = dict()

    assert toolchain is not None, "Empty toolchain parameter provided"

    # If no code will be executed with the toolchain env,
    # why bother setting it up in the first place?
    if and_then is None:
        return

    toolchain_script = tb.config.get(f"""\
toolchains.{toolchain}.env_setup_script""")

    tb.log.doc_log(f"""
### Setting up the toolchain ###
Setup the `{toolchain}` toolchain by calling its env script:
""")

    # Create an env shell
    with tb.new_shell(tbot.shell.sh_env.ShellShEnv) as tbn:
        tbn.shell.exec0(f"source {toolchain_script}")

        tbn.call(and_then, **params)
