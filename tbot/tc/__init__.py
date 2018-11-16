import typing
import tbot
import traceback


@tbot.testcase
def testsuite(*args: typing.Callable, **kwargs: typing.Any) -> None:
    errors: typing.List[typing.Tuple[str, str]] = []

    for test in args:
        try:
            test(**kwargs)
        except Exception:
            errors.append((test.__name__, traceback.format_exc()))

    with tbot.log.message(
        tbot.log.c(
            tbot.log.u(
                "────────────────────────────────────────",
                "----------------------------------------",
            )
        ).dark
    ) as ev:
        if errors != []:
            ev.writeln(
                tbot.log.c("Failure").red.bold
                + f": {len(errors)}/{len(args)} tests failed\n"
            )
            for tc, err in errors:
                tbot.log.message(tbot.log.c(tc).blue + ":\n" + err)
            raise Exception(f"{len(errors)}/{len(args)} tests failed")
        else:
            ev.writeln(
                tbot.log.c("Success").green.bold
                + f": {len(args)}/{len(args)} tests passed"
            )
