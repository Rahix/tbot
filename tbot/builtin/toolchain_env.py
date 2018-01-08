""" Testcase to setup toolchain environment """
import tbot.shell.sh_env


@tbot.testcase
def toolchain_env(tb, toolchain=None, and_then=None, params=None):
    """ Setup a toolchain environment and call a testcase inside """
    if params is None:
        params = dict()

    if not tb.shell.shell_type[0] == "sh":
        raise "Need an sh shell"

    if toolchain is None:
        raise "Empty toolchain parameter provided"

    # If no code will be executed with the toolchain env,
    # why bother setting it up in the first place?
    if and_then is None:
        return

    toolchain_script = tb.config.get(f"""\
toolchains.{toolchain}.env_setup_script""")

    # Create an env shell
    with tb.new_shell(tbot.shell.sh_env.ShellShEnv) as tbn:
        tbn.shell.exec0(f"source {toolchain_script}")

        tbn.call(and_then, **params)
