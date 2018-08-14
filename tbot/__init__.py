import typing
import functools
from tbot import log

from . import selectable  # noqa: F401
from .selectable import acquire_lab, acquire_board, acquire_uboot  # noqa: F401

F = typing.TypeVar("F", bound=typing.Callable[..., typing.Any])


def testcase(tc: F) -> F:
    """Decorate a function to make it a testcase."""

    @functools.wraps(tc)
    def wrapped(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
        log.testcase_begin(tc.__name__)
        try:
            result = tc(*args, **kwargs)
        except:  # noqa: E722
            log.testcase_end(False)
            raise
        log.testcase_end()
        return result

    wrapped._tbot_testcase = True  # type: ignore
    return typing.cast(F, wrapped)
