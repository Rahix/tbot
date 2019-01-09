.. highlight:: guess
   :linenothreshold: 3

Quick Start
===========

Commandline
-----------
First of all, install tbot.  Instructions are here: :ref:`install:Installation`.

Let's get started!  To check if the installation went smoothly, try running tbot's selftests::

    $ tbot selftest

If you feel adventurous, there are even more selftests that check if the built-in testcases
work as intended.  Of course, these can't test board-related functionality, but it's a start::

    $ tbot selftest_tc

tbot also allows you to run multiple testcases at once::

    $ tbot selftest selftest_tc

If you want an overview of the available testcases, use this command::

    $ tbot --list-testcases

----

The output you saw during the testcase runs was just a rough overview of what is going on.  That
might not be detailed enough for you.  By adding ``-v``, tbot will show all commands as they are
executed.  Add another one: ``-vv`` and you will also see command outputs!

::

    $ tbot selftest_path_stat -vv

.. note::
    There is one more verbosity level: ``-vvv``.  This is for debugging, if something doesn't quite work.
    It shows you all communication happening, both directions.  Try it if you want to, but be prepared:
    It will look quite messy!

One more commandline feature before we dive into python code:  If you are afraid of a destructive
command, you can run tbot with ``--interactive``::

    $ tbot selftest_uname -vi

Now tbot will kindly ask you before running each command!  (See? ``-emacs`` wouldn't answer as nicely!)

Testcases
---------
Ok, commandline isn't all that fun.  Let's dive deeper!  Some code please!

::

    import tbot

    @tbot.testcase
    def hello_world():
        tbot.log.message("Hello World!")

This is tbot's hello world.  Stick this code into a file named ``tc.py``.  Now, if you check the list
of testcases (``tbot --list-testcases``), ``hello_world`` pops up.  Run it!

::

    $ tbot hello_world

Hello tbot!

.. note::
    I am sure at least one person reading this will be offended by being told how to name their file.
    Why ``tc.py``?  I prefer calling it ``my_most_amazing_testcases.py``!

    Fear not, you can do just that!  You just need to tell tbot about it.  Instead of the above
    command, run::

        $ tbot -t my_most_amazing_testcases.py hello_world

    You can also include all python files in a directory with ``-T``.

Well, before writing actual tests, I need to explain a few things:  In tbot, testcases are basically
python functions.  This means you can call them just like python functions!  From other testcases!
How about the following?

::

    import tbot

    @tbot.testcase
    def greet(name: str) -> None:
        tbot.log.message(f"Hello {name}!!")

    @tbot.testcase
    def greet_tbot() -> None:
        greet("tbot")

If you now call ``greet_tbot``, you can see in the output that it calls ``greet``.

But wait! If you try calling ``greet`` directly, it fails!  Of course, because ``greet`` has a
parameter.  As previously mentioned, testcases are python functions, so naturally, they can also have
parameters.  There are two ways to "fix" this:

1. Specifying a default value for the parameter::

    import tbot

    @tbot.testcase
    def greet(name: str = "World") -> None:
        tbot.log.message(f"Hello {name}!!")

2. Setting a value for the parameter!  That's right, you can set the parameter from the commandline.  It looks
   like this::

    $ tbot greet -p name=\"tbot\"

   Note the escaped quotes around ``\"tbot\"``.  They are necessary because the value is `eval()`-uated
   internally.  This is done to allow you to set values of any type with ease.  Any python
   expression goes!  (Also evil ones, be careful ...)

As you'll see later on, there are cases where you should have default values and ones where
it doesn't make sense.  You'll have to decide individually ...

Machines
--------
Next up: Machines!  Machines are what tbot is made for.  Let's take a look at the diagram from the
landing page again:

.. image:: _static/tbot.svg

Lab-host? It's a machine! Buildhost?  Just as well!  The boards you are testing?  You guessed it!

Let's start simple though:  Just run a command on the lab-host::

    import tbot

    @tbot.testcase
    def greet_user() -> None:
        with tbot.acquire_lab() as lh:
            name = lh.exec0("id", "--user", "--name").strip()

            tbot.log.message(f"Hello {name}!")

Now try::

    $ tbot greet_user -v

As you can see, tbot ran ``whoami`` to find your name.  You might be curious about the ``[local]``
part: That's the machine tbot ran the command on.  By default, the lab-host is your localhost. We'll
see later how to change that.

There are quite a few new things in the sample above.  Let's go through them one by one:

* :func:`tbot.acquire_lab`: This is a function provided by tbot that returns the selected lab-host.
* ``with tbot.acquire_lab() as lh:``: Each machine is a context manager.  To get access, you need
  to enter its context and as soon as you leave it the connection is destroyed.  If you haven't
  heard about context managers before, take a look at `Python with Context Managers
  <https://jeffknupp.com/blog/2016/03/07/python-with-context-managers/>`_.  They are really useful!
* :meth:`lh.exec0() <tbot.machine.linux.LinuxMachine.exec0>`:  This is a function to run a command.
  Specifically **exec**-utes it and checks whether the return value is ``0``.  There are also others, for
  example, :meth:`lh.test() <tbot.machine.linux.LinuxMachine.test>` which returns ``True`` if the command
  succeeded and ``False`` otherwise.
* All command executing methods take one parameter per commandline argument.  Each one will be properly
  escaped:  ``lh.exec0("echo", "!?#;>&<")`` would print ``!?#;>&<``, no manual quoting needed!
* :meth:`lh.exec0() <tbot.machine.linux.LinuxMachine.exec0>` returns a string which I call ``.strip()``
  on.  The reason is that most commands include a trailing newline (``\n``).  I don't want that in the
  name so I remove it.

Machines have quite an extensive set of functionality that is definitely worth checking out.  Link
is here:

.. todo::
    Machine docs

One more feature I want to mention in this quick guide:  Most machines have an
:meth:`~tbot.machine.linux.LinuxMachine.interactive` method.  This method will connect the
channel to the terminal and allows you to directly enter commands.  You can use it to make tbot
do some work, then do something manually.  Like a symbiotic development process.  It really makes
you a lot more productive if you embrace this idea!  There is also a testcase to call it from the
commandline::

    $ tbot interactive_lab

Configuration
-------------
Up until now we did everything on our localhost.  That's boring!  tbot allows you to easily use a
lab-host that you can connect to via SSH for example.  To do that you have to write a small config
file.  There's a twist though!  The config file is actually a python module.  In this module, you
create a class for your lab-host.  If you have some special features on your lab-host you can add
them in there just as well!

The simplest config looks like this::

    import tbot
    from tbot.machine import linux

    class AwesomeLab(linux.lab.SSHLabHost):
        name = "awesome-lab"
        hostname = "awesome.lab.com"

        @property
        def workdir(self):
            return linux.Workdir.athome(self, "tbot-workdir")


    # tbot will check for `LAB`, don't forget to set it!
    LAB = AwesomeLab

Of course, you'll have to adjust this a little.  tbot will try to connect to the host ``hostname``.
It will query ``~/.ssh/config`` for a ``username`` and key.  (You need to be able to connect
to ``hostname`` without a password!)

Try using your config now!

::

    $ tbot -l <name-of-lab-config>.py interactive_lab

Congratulations! You now have a remote session on your lab-host!  You could also run some selftest to verify
that tbot can run these commands on your new lab-host as well::

    $ tbot -l lab.py selftest_path_integrity -vv

As you can see, now it says ``[awesome-lab]`` in front of the commands.  tbot is running commands
remotely!

This was just a simple example ... Configs can get a lot bigger and a lot more complex.  Take a
look at :ref:`their docs <config:Configuration>` for more info!


Hardware Interaction
--------------------
We haven't even talked to actual hardware yet!  Let's change that.  Unfortunately, as each device
is different, you'll have to figure out a few things yourself.

First Step:  Another config file.  The board needs to be configured in a second file.  I'll show
you a heavily commented example.  Change it to match your hardware!  I'll separate it into parts
that we add as we go.  This is the first::

    import tbot
    from tbot.machine import board, channel, linux

    class SomeBoard(board.Board):
        name = "some-board"

        def poweron(self) -> None:
            """Procedure to turn power on."""

            # You can access the labhost as `self.lh`
            # In this case I have a simple command to toggle power.
            self.lh.exec0("remote_power", "bbb", "on")

            # If you can't automatically toggle power,
            # you have to insert some marker here that reminds you
            # to manually toggle power.  How about:
            tbot.log.message("Turn power on now!")

        def poweroff(self) -> None:
            """Procedure to turn power off."""
            self.lh.exec0("remote_power", "bbb", "off")

        def connect(self) -> channel.Channel:
            """Connect to the boards serial interface."""

            # `lh.new_channel` creates a new channel and runs the
            # given command to connect.  Your command should just
            # connect its tty to the serial console like rlogin,
            # telnet, picocom or kermit do.  The minicom behavior
            # will not work.
            return self.lh.new_channel("connect", "bbb")

    # tbot will check for `BOARD`, don't forget to set it!
    BOARD = SomeBoard

If you did everything correctly, this should be enough to get a serial connection running.  Try this::

    $ tbot -l lab.py -b my-board.py interactive_board -vv

You should see the board starting to boot.  If not, go back and check manually if the commands by
themselves work.

Next up we will add config for the Linux running on the board.  I'll skip U-Boot in this quick guide
for simplicity.  Here's the full new config::

    import tbot
    from tbot.machine import board, channel, linux

    class SomeBoard(board.Board):
        name = "some-board"

        def poweron(self) -> None:
            self.lh.exec0("remote_power", "bbb", "on")

        def poweroff(self) -> None:
            self.lh.exec0("remote_power", "bbb", "off")

        def connect(self) -> channel.Channel:
            return self.lh.new_channel("connect", "bbb")

    # Linux machine
    # We use a `LinuxStandaloneMachine` in this case, because we
    # do not care about U-Boot.
    class SomeBoardLinux(board.LinuxStandaloneMachine[SomeBoard]):
        # Username for logging in once linux has booted
        username = "root"
        # Password.  If you don't need a password, set this to `None`
        password = "~ysu0dbi"
        # Specifying the shell type is really important!  Else you will
        # see weird things happening.  Login manually once to find out
        # which shell you are running and then set it here.
        shell = linux.shell.Ash

    BOARD = SomeBoard
    # You need to set `LINUX` now as well.
    LINUX = SomeBoardLinux

Again, adjust it as necessary.  If you are unsure about some parameters, you can check in the
``interactive_board`` session.

If you set everything correctly, you should be able to run::

    $ tbot -l lab.py -b my-board.py interactive_linux -vv

You now have a shell on the board!  As before, you can also try running a selftest::

    $ tbot -l lab.py -b my-board.py selftest_board_linux -vv

Nice!

----

Last part of this guide will be interacting with the board from a testcase.  It's pretty straight
forward::

    import tbot

    @tbot.testcase
    def test_board() -> None:
        # Get access to the lab-host as before
        with tbot.acquire_lab() as lh:
            # This context is for the "hardware".  Once you enter
            # it, the board will be powered on and as soon as
            # you exit it, it will be turned off again.
            with tbot.acquire_board(lh) as b:
                # This is the context for the "LinuxMachine".
                # Entering it means tbot will listen to the
                # board booting and give you a machine handle
                # as soon as the shell is available.
                with tbot.acquire_linux(b) as lnx:
                    lnx.exec0("uname", "-a")

Those two additional indentation levels aren't nice - We can refactor the code to
look like this (I showed the explicit version first so you can see what is going on)::

    import contextlib
    import tbot

    @tbot.testcase
    def test_board() -> None:
        with contextlib.ExitStack() as cx:
            lh  = cx.enter_context(tbot.acquire_lab())
            b   = cx.enter_context(tbot.acquire_board(lh))
            lnx = cx.enter_context(tbot.acquire_linux(b))

            lnx.exec0("uname", "-a")

There is still one issue with this design:  Let's pretend this is a test to check some
board functionality.  Maybe you have quite a few testcases that each check different
parts.  Now, we want to call all of them from some "master" test, so we can test everything
at once.

The issue we will run into is that each testcase will A) reconnect to the lab-host and
B) powercycle the board.  This will be very very slow!  We can do better!

The idea is that testcases take the lab and board as optional parameters.  This allows
reusing the old connection and won't powercycle the board for each test (if you need
powercycling, you can of course do it like above)::

    import contextlib
    import typing
    import tbot
    from tbot.machine import linux, board

    @tbot.testcase
    def test_board(
        lab: typing.Optional[linux.LabHost] = None,
        board_linux: typing.Optional[board.LinuxMachine] = None,
    ) -> None:
        with contextlib.ExitStack() as cx:
            if board_linux is None:
                lh  = cx.enter_context(lab or tbot.acquire_lab())
                b   = cx.enter_context(tbot.acquire_board(lh))
                lnx = cx.enter_context(tbot.acquire_linux(b))
            else:
                lnx = board_linux

            lnx.exec0("uname", "-a")

    @tbot.testcase
    def call_it() -> None:
        with tbot.acquire_lab() as lh:
            test_board(lh)

You can still call ``test_board`` from the commandline, but ``call_it`` works as well!

You will probably need this pattern quite a lot.  I have compiled a page of this and
similar patterns that you can easily copy to your code: :ref:`recipes:Recipes`

That's it for the quick-start.  I hope I got you hooked!  The next step is to look deeper into
each individual part.  Docs are here:

.. todo::
    More docs
