import typing
import tbot


@tbot.testcase
def testsuite(*args: typing.Callable, **kwargs: typing.Any) -> None:
    errors: typing.List[Exception] = []

    for test in args:
        try:
            test(**kwargs)
        except Exception as e:
            errors.append(e)

    if errors != []:
        raise Exception(f"{len(errors)}/{len(args)} tests failed")
