.. tbot getting started guide

Getting Started
===============

The main concept of TBot is, that everything is a testcase. Testcases
can call other testcases like you would call a function to do a certain
task. For example the :func:`uboot_checkout_and_build`
testcase builds a version of U-Boot for your currently selected board.

You could do so, by calling TBot like this::

    $ tbot <lab-name> <board-name> uboot_checkout_and_build

where ``lab-name`` is the name of the config for your lab host (more on that later)
and ``board-name`` is the name of the config for your board.

If you want to call the testcase from another testcase instead (in python),
it would look like this::

    import tbot

    @tbot.testcase
    def an_example_testcase(tb: tbot.TBot) -> None:
        tb.call("build_uboot")

Now you can call your testcase like this::

    $ tbot <lab-name> <board-name> an_example_testcase

Note the decorator for this function: ``tbot.testcase`` makes a function a testcase
that can be called by other testcases or from the commandline.

Testcases can also take parameters and return values::

    import tbot

    @tbot.testcase
    def a_testcase_with_a_parameter(tb: tbot.TBot, *,
                                    param_mandatory: bool,
                                    param_optional: bool = False,
                                   ) -> bool:
        tbot.log.message(f"A: {param_mandatory}, B: {param_optional}")
        return param_mandatory or param_optional

When you try to call this testcase from the commandline, you will notice TBot failing
with an error that says something about a missing parameter. And that is entirely
reasonable because the testcase takes a mandatory argument (Arguments after a
``*`` are called *Mandatory Keyword-Argumens*). You can pass that parameter to TBot
like this::

    $ tbot <lab-name> <board-name> a_testcase_with_a_parameter -p param_mandatory=True

TBot will evaluate everything after the ``=`` as a python expression. And of course, the
optional parameter can also be set in the same way.

To get the return value of a testcase, you have to call it from another testcase, like this::

    ret_val = tb.call("a_testcase_with_a_parameter", param_mandatory=False, param_optional=True)
    assert ret_val is True

Lab host shell interaction
--------------------------

Testcases can interact with the shell of the lab host. This might look like the
following::

    import tbot

    @tbot.testcase
    def shell_interaction(tb: tbot.TBot) -> None:
        # exec0 executes a command and expects a return code of 0
        # and will raise an exception otherwise
        out = tb.shell.exec0("echo Hello World")
        assert out == "Hello World\n", "%r is not Hello World" % out

        # exec executes a command and returns a tuple (ret_code, output)
        ret_code, _ = tb.shell.exec("false")
        assert ret_code == 1, "%r is not 1" % ret_code

There are a few things happening here: First of all, ``tb.shell`` is just a shortcut
for ``tb.machines["labhost"]``, which, by default but not always, is mapped to
``tb.machines["labhost-noenv"]``. ``noenv`` means, each command is run in an isolated
environment and setting environment vars or changing the working directory will
not affect other commands. You should use this type of machine, whenever possible as
this reduces sideeffects and with that minimizes the risk of strange bugs occuring.

In some cases however, you need a shell, that keeps its environment and working
directory. For that, tbot has an ``env`` machine. You can use it like this::

    import tbot

    @tbot.testcase
    def envshell_demo(tb):
        with tb.machine(tbot.machine.MachineLabEnv()) as tb:
            tb.shell.exec0("FOO='bar'")

            out = tb.shell.exec0("echo $FOO")
            assert out == "bar\n"


Board interaction
-----------------

In a similar fashion, you can interact with the U-Boot/Linux shell of your board.
TBot will automatically turn on the board and make sure it is turned off, when
your testcase is done. It might be looking like the following (U-Boot)::

    import tbot

    @tbot.testcase
    def boardshell_demo_uboot(tb):
        with tb.with_board_uboot() as tb:
            tb.boardshell.exec0("version")

        # Board is powered off after the end of the with statement

(Linux)::

    import tbot

    @tbot.testcase
    def boardshell_demo_linux(tb):
        with tb.with_board_linux() as tb:
            tb.boardshell.exec0("uname -a")

        # Board is powered off after the end of the with statement

It is also possible to do something in U-Boot before booting Linux::

    import tbot

    @tbot.testcase
    def boardshell_demo_uboot_and_linux(tb):
        with tb.with_board_uboot() as tb:
            # Do things in U-Boot
            tb.boardshell.exec0("version")

            with tb.with_board_linux() as tb:
                # Do things in Linux (Linux was started without
                # powercycling, so changes made in U-Boot will
                # still be effective)
                tb.boardshell.exec0("uname -a")

            # Back to U-Boot, TBot has powercycled the board
            tb.boardshell.exec0("version")

        # Board is powered off after the end of the with statement

