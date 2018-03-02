"""
Testcase to setup a toolchain environment
-----------------------------------------
"""
import typing
import tbot

EXPORT = ["Toolchain", "UnknownToolchainException"]

class UnknownToolchainException(Exception):
    """ The toolchain provided was not found in the config """
    pass

class Toolchain(str):
    """ A meta object to represent a toolchain """
    pass

@tbot.testcase
def toolchain_get(tb: tbot.TBot, *, name: typing.Optional[str] = None) -> Toolchain:
    """
    Get a toolchain and ensure it exists

    :param name: Name of the toolchain, defaults to ``tb.config["board.toolchain"]``
    :returns: The toolchain meta object to be passed to testcases that need a toolchain
    """
    name = name or tb.config["board.toolchain"]
    if tb.config[f"toolchains.{name}", None] is None:
        raise UnknownToolchainException(repr(name))
    tb.log.log_debug(f"Toolchain '{name}' exists")
    return Toolchain(name)

@tbot.testcase
def toolchain_env(tb: tbot.TBot, *,
                  toolchain: Toolchain,
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

    # We don't need to check if the toolchain exists because it has to
    # (You can't create a Toolchain() object without it existing)

    toolchain_script = tb.config[f"toolchains.{toolchain}.env_setup_script"]

    tb.log.log_debug(f"Setting up '{toolchain}' toolchain")

    tb.log.doc_log(f"""Setup the `{toolchain}` toolchain by calling its env script:
""")

    # Create an env shell
    with tb.machine(tbot.machine.MachineLabEnv()) as tbn:
        tbn.shell.exec0(f"unset LD_LIBRARY_PATH")
        tbn.shell.exec0(f"source {toolchain_script}")

        tbn.call(and_then, **params)
