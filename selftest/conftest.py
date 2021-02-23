from typing import Any, Callable, ContextManager, Iterator

import pytest
import tbot

import testmachines


@pytest.fixture(scope="session")
def tbot_context() -> Iterator[tbot.Context]:
    tbot.log.VERBOSITY = tbot.log.Verbosity.STDOUT
    tbot.log.NESTING = 1
    with tbot.Context(keep_alive=True, reset_on_error_by_default=True) as ctx:
        testmachines.register_machines(ctx)

        yield ctx


AnyLinuxShell = Callable[[], ContextManager[tbot.machine.linux.LinuxShell]]


@pytest.fixture(
    scope="module",
    params=[
        testmachines.LocalhostBash,
        testmachines.LocalhostSlowBash,
        testmachines.LocalhostAsh,
        testmachines.MocksshClient,
    ],
)
def any_linux_shell(tbot_context: tbot.Context, request: Any) -> AnyLinuxShell:
    def inner() -> ContextManager[tbot.machine.linux.LinuxShell]:
        return tbot_context.request(request.param)

    return inner
