.. tbot getting started guide

Getting Started with TBot
=========================

The main concept of tbot is, that everything is a testcase. Testcases
can call other testcases like you would call a function to do a certain
task. For example the :func:`uboot_checkout_and_build`
testcase builds a version of U-Boot for your currently selected board.

You could do so, by calling tbot like this::

    $ tbot <lab-name> <board-name> uboot_checkout_and_build

where ``lab-name`` is the name of the config for your lab host (more on that later)
and ``board-name`` is the name of the config for your board.

If you want to call the testcase from another testcase instead (in python),
it would look like this::

    import tbot

    @tbot.testcase
    @tbot.cmdline
    def an_example_testcase(tb):
        tb.call("build_uboot")

Now you can call your testcase like this::

    $ tbot <lab-name> <board-name> an_example_testcase

Note the 2 decorators for this function ``tbot.testcase`` makes a function a testcase
that can be called by other testcases and ``tbot.cmdline`` allows the testcase to be
called from the command line (like the command above). Only use ``tbot.cmdline`` if your
testcase does not have any mandatory parameters, else calling it will not work.

Lab host shell interaction
--------------------------

Testcases can interact with the shell of the lab host. This might look like the
following::

    import tbot

    @tbot.testcase
    @tbot.cmdline
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
    @tbot.cmdline
    def envshell_demo(tb):
        with tb.machine(tbot.machine.MachineLabEnv()) as tbn:
            tbn.shell.exec0("FOO='bar'")

            out = tbn.shell.exec0("echo $FOO")
            assert out == "bar\n"


Board interaction
-----------------

In a similar fashion, you can interact with the U-Boot shell of your board.
TBot will automatically turn on the board and make sure it is turned off, when
your testcase is done. It might be looking like the following::

    import tbot

    @tbot.testcase
    @tbot.cmdline
    def boardshell_demo(tb):
        with tb.with_boardshell() as tbn:
            tbn.boardshell.exec0("version")

        # Board is powered off after the end of the with statement
