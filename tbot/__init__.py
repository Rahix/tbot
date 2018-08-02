import typing
from tbot import log

F = typing.TypeVar('F', bound=typing.Callable[..., typing.Any])


def testcase(tc: F) -> F:
    """Decorate a function to make it a testcase."""
    def wrapped(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
        log.testcase_begin(tc.__name__)
        try:
            result = tc(*args, **kwargs)
        except:  # noqa: E722
            log.testcase_end(False)
            raise
        log.testcase_end()
        return result
    return typing.cast(F, wrapped)
