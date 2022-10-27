import typing
import tbot
import traceback


@tbot.testcase
def testsuite(*args: typing.Callable, **kwargs: typing.Any) -> None:
    """
    Run a number of tests and report how many of them succeeded.

    .. note::

        If your goal is implementing a large testsuite using
        tbot, you may want to look at integrating tbot with
        `pytest <https://pytest.org/>`_ instead of using this
        function.

        Check the :ref:`pytest-integration` guide for more info.

    :param args: Testcases
    :param kwargs: Named-Arguments that should be given to each testcase.
        Be aware that this requires all testcases to have compatible
        signatures.

    **Example**::

        import tbot
        from tbot import tc, machine

        @tbot.testcase
        def test_a(lab: machine.linux.LinuxShell) -> None:
            lab.exec0("echo", "Test", "A")

        @tbot.testcase
        def test_b(lab: machine.linux.LinuxShell) -> None:
            lab.exec0("uname", "-a")

        @tbot.testcase
        def all_tests() -> None:
            with tbot.acquire_lab() as lh:
                tc.testsuite(
                    test_a,
                    test_b,

                    lab=lh,
                )
    """
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
