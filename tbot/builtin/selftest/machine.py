import tbot


@tbot.testcase
def selftest_with_machine(tb: tbot.TBot) -> None:
    tbot.log.message("Trying with different name ...")
    tb1 = tb
    with tb.machine(tbot.machine.MachineLabNoEnv()) as tbn:
        tb2 = tbn
    tb3 = tb

    assert tb1 is not tb2, "New machine was not created correctly"
    assert tb1 is tb3, "New machine was not destructed correctly"

    del tb1
    del tb2
    del tb3

    tbot.log.message("Trying with same name ...")
    tb1 = tb
    with tb.machine(tbot.machine.MachineLabNoEnv()) as tb:
        tb2 = tb
    tb3 = tb

    assert tb1 is not tb2, "New machine was not created correctly"
    # This check does not work because the name from inside the with
    # statement now in the outer scope. TBot() contains a fix for this,
    # but that fix can't change where a reference is pointed

    # assert tb1 is tb3, "New machine was not destructed correctly"
    assert tb1.machines is tb3.machines, "New machine was not destructed correctly"
