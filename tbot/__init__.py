import typing

F = typing.TypeVar('F', bound=typing.Callable[..., typing.Any])


def testcase(tc: F) -> F:
    """Decorate a function to make it a testcase."""
    def wrapped(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
        print(f"Testcase {tc.__name__} ...")
        result = tc(*args, **kwargs)
        print(f"Done.")
        return result
    return typing.cast(F, wrapped)
