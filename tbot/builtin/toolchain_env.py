"""
Testcase to setup a toolchain environment
-----------------------------------------
"""
import typing
import tbot


@tbot.testcase
def toolchain_env(tb: tbot.TBot,
                  toolchain: typing.Optional[str] = None,
                  and_then: typing.Union[str, typing.Callable, None] = None,
                  params: typing.Optional[typing.Dict[str, typing.Any]] = None) -> None:
    """
    Setup a toolchain environment and call a testcase inside

    :param toolchain: Which toolchain to use
    :param and_then: What testcase to call inside the env
    :param params: Parameters for the testcase
    """
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
    with tb.machine(tbot.machine.MachineLabEnv()) as tbn:
        tbn.shell.exec0(f"unset LD_LIBRARY_PATH")
        tbn.shell.exec0(f"source {toolchain_script}")

        tbn.call(and_then, **params)
