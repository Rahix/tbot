.. tbot getting started guide

.. highlight:: guess
   :linenothreshold: 3

Getting Started
===============

TBot Project Structure
----------------------
First of all you need to create a new TBot project. TBot has a handy
tool for doing so called ``tbot-mgr``. To start a new project use the
following command::

    ~$ tbot-mgr new test-tbot-project

``tbot-mgr`` will create a new folder called ``test-tbot-project`` and
a few subfolders below it that TBot expects. The structure of a TBot
project looks like this::

    +-test-tbot-project/
      +-config/
      | +-boards/
      | | +-board1.py
      | | +-board2.py
      | +-labs/
      |   +-lab1.py
      |   +-lab2.py
      +-tc/
        +-testcases1.py
        +-testcases2.py

``config/boards/`` contains a file for each board in your project,
``config/labs/`` contains a file for each lab in your project.

``tc/`` contains files that will be read by TBot when collecting testcases.
You can write as many testcases in one file as you want.

First TBot Usage
----------------
Now would be a good time to test if TBot actually works. To do so, use
``tbot-mgr`` to create a dummy board and lab::

    ~/test-tbot-project$ tbot-mgr add dummies

And then run TBot's selftests::

    ~/test-tbot-project$ tbot dummy-lab dummy-board selftest -v

What you can see now is what the output of TBot while running a testcase looks like.
``-v`` controls the verbosity level.

.. note::
    The dummy-lab that ``tbot-mgr`` just created is a lab that will try to connect to
    localhost via ssh. This means you **have to** have an sshd running. If your ssh
    daemon runs with a config that does not use the default settings, please adjust the
    file ``test-tbot-project/config/labs/dummy-lab.py`` accordingly.

If all went well, the last line of TBot's output should mention a success. If that is
the case, you are set for writing your own testcases:

Testcases
---------
The main concept of TBot is, that everything is a testcase. Testcases
can call other testcases like you would call a function to do a certain
task. For example the :func:`~tbot.builtin.uboot.uboot_tasks.uboot_checkout_and_build`
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

.. warning::
   TBot uses **eval** for those parameters. This could become a security issue
   if you use untrusted input for constructing the commandline. Be careful!

To get the return value of a testcase, you have to call it from another testcase, like this::

    ret_val = tb.call("a_testcase_with_a_parameter", param_mandatory=False, param_optional=True)
    assert ret_val is True

Labhost Shell Interaction
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


.. note::
   The ``noenv`` shell is implemented by creating a new SSH channel for each command.
   This guarantees the most isolation possible. The ``env`` shell however starts a
   remote interactive bash and executes commands in there. This makes it behave as if
   the user were to enter the commands by hand but has a few ugly side effects:

   TBot has to use a custom prompt to detect when a command finishes. This is ok as long
   as you don't send a command like ``tb.shell.exec0("PS1='fooled-you! '")`` which would
   make TBot hang because the expected prompt never arrives. This might seem like a stupid
   thing to do, but it actually has some implications: For example the python virtualenv
   adds a string to your prompt by default. Just keep this in mind when using ``env`` shells ...

   In the same spirit, there are a few other commands that can lead to unexpected behaviour.
   Just be careful. As long as you just use commands that a user would normally use, you should
   be fine. If you think that something should work but doesn't, feel free to open an issue.


Board Interaction
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


Buildhost Interaction
---------------------
TBot uses a host different from the labhost for building software. The rationale
behind this is, that the labhost is used by everyone and is connected to a lot
of boards and building on there would make the experience worse for ther users.

To just connect to the buildhost, you could do something like this::

    import tbot


    @tbot.testcase
    def buildhost_example(tb: tbot.TBot) -> None:
        with tb.machine(tbot.machine.MachineBuild()) as tb:
            tb.shell.exec0("uname -a")

Note how ``tb.shell`` no longer is the labhost but now runs commands on the buildhost.
This allows running a testcase on both the labhost and the buildhost without having
to write it twice.

Another option to access the buildhost is to make use of TBot's knowledge of toolchains.
The following code will connect to the buildhost and initialize the toolchain for the
current board. This makes it easier to write code to compile something.

::

    import tbot


    @tbot.testcase
    def buildhost_toolchain(tb: tbot.TBot) -> None:
        # Get the default toolchain for the current board
        toolchain = tb.call("toolchain_get")

        buildhost_workdir = None
        @tb.call_then("toolchain_env", toolchain=toolchain)
        def build(tb: tbot.TBot) -> None:
            cc = tb.shell.exec0("echo $CC").strip()
            tbot.log.message(f"Compiler: '{cc}'")
            # Build your project, for portability, do it inside
            # "tb.shell.workdir"
            buildhost_workdir = tb.shell.workdir / "my-project"
            tb.shell.exec0(f"mkdir -p {buildhost_workdir}")

        # Use this testcase to retrieve you build results
        labhost_file = tb.call(
            "retrieve_build_artifact",
            buildfile=buildhost_workdir / "result.bin",
        )

.. highlight:: python
   :linenothreshold: 3

``tb.and_then``
---------------
A new syntax that we can see here is ``@tb.call_then``. This is a shorthand for writing::

    def build(tb: tbot.TBot) -> None:
        pass

    tb.call("toolchain_env", toolchain=toolchain, and_then=build)

Some testcases take a testcase as a parameter that will be run after setting up some
environment. In this case, the ``toolchain_env`` testcase connects to the buildhost,
sets up the toolchain and then runs our testcase - As we can see, the ``CC`` environment
variable now contains the proper compiler.

.. seealso::
   Another testcase that makes use of this ``and_then`` syntax is :func:`~tbot.builtin.git_tasks.git_bisect`


``tbot.log`` - Logging
----------------------
TBot has its own logging system. It is available as ``tbot.log``. As you can see, the simplest way to use it
is to use::

    tbot.log.message("msg")
    # or
    tbot.log.debug("msg")

To see the output from the debug message, you need to add a ``-v`` commandline argument. If you add ``-vv`` you will
also see all commands that are run. Another ``v``: ``-vvv`` will also show the output of every command.

.. seealso::
   More information on logging can be found under :ref:`tbot-logging` or in the module itself: :mod:`tbot.log`

Configuration
-------------
All of the above can be used with the dummy config that we created in the beginning. But it would be way more interesting
to to all this using actual hardware. For that, you first need to set up configuration.

Start by creating a lab config. If you have a remote labhost where your board is connected, use::

    $ tbot-mgr add lab

and follow the instructions on screen.

If your board and it's power is directly connected to your own computer, you can use

    **TODO**


To check your lab config, create a dummy-board and run TBot's selftests::

    $ tbot-mgr add dummy-board -n <my-lab>-dummy -l <my-lab>
    $ tbot <my-lab> <my-lab>-dummy selftest

If those pass, you are done. If not, open ``config/labs/<my-lab>.py`` and adjust it
so the tests pass. See :ref:`tbot-cfg-opts` for available config keys.

Next we need to create a board config. Use::

    $ tbot-mgr add board -l <my-lab>

to do so.Run selftests again, this time using your board to verify your board config::

    $ tbot <my-lab> <my-board> selftest

This of course requires your board to already have a version of U-Boot installed. TBot can't do this first setup for you,
but you could write a testcase for installing a new version of U-Boot that you compiled using ``uboot_checkout_and_build`` ;)

If something fails, adjust ``config/boards/<my-board>.py``, see :ref:`tbot-cfg-opts` for available config keys.
