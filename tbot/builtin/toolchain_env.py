"""
Testcase to setup a toolchain environment
-----------------------------------------
"""
import typing
import tbot


class UnknownToolchainException(Exception):
    pass

@tbot.testcase
def toolchain_env(tb: tbot.TBot, *,
                  toolchain: str,
                  and_then: typing.Union[str, typing.Callable],
                  params: typing.Optional[typing.Dict[str, typing.Any]] = None) -> None:
    """
    Setup a toolchain environment and call a testcase inside

    :param toolchain: Which toolchain to use
    :param and_then: What testcase to call inside the env
    :param params: Parameters for the testcase
    """
    if params is None:
        params = dict()

    # Check if the toolchain exists
    if tb.config[f"toolchains.{toolchain}", None] is None:
        raise UnknownToolchainException(repr(toolchain))

    toolchain_script = tb.config[f"toolchains.{toolchain}.env_setup_script"]

    tb.log.log_debug(f"Setting up '{toolchain}' toolchain")

    tb.log.doc_log(f"""Setup the `{toolchain}` toolchain by calling its env script:
""")

    # Create an env shell
    with tb.machine(tbot.machine.MachineLabEnv()) as tbn:
        tbn.shell.exec0(f"unset LD_LIBRARY_PATH")
        tbn.shell.exec0(f"source {toolchain_script}")

        tbn.call(and_then, **params)
