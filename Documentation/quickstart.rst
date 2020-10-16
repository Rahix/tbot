.. highlight:: guess
   :linenothreshold: 3

.. _quickstart:

Quick Start
===========

Commandline
-----------
First of all, install tbot.  Instructions are here: :ref:`installation`.

Let's get started!  To check if the installation went smoothly, try running tbot's selftests:

.. html-console::

    <pre>bash-4.4$ tbot selftest
    <font color="#F4BF75"><b>tbot</b></font> starting ...
    ├─Calling <font color="#A1EFE4"><b>selftest</b></font> ...
    │   ├─Calling <font color="#A1EFE4"><b>testsuite</b></font> ...
    │   │   ├─Calling <font color="#A1EFE4"><b>selftest_failing</b></font> ...
    │   │   │   ├─Calling <font color="#A1EFE4"><b>inner</b></font> ...
    │   │   │   │   └─<font color="#F92672"><b>Fail</b></font>. (0.000s)
    │   │   │   └─<font color="#A6E22E"><b>Done</b></font>. (0.001s)
    │   │   ├─Calling <font color="#A1EFE4"><b>selftest_uname</b></font> ...
    │   │   │   └─<font color="#A6E22E"><b>Done</b></font>. (0.003s)
    │   │   ├─Calling <font color="#A1EFE4"><b>selftest_user</b></font> ...
    │   │   │   └─<font color="#A6E22E"><b>Done</b></font>. (0.001s)
    [...]
    │   │   ├─Calling <font color="#A1EFE4"><b>selftest_board_linux</b></font> ...
    │   │   │   ├─<font color="#F4BF75"><b>Skipped</b></font> because no board available.
    │   │   │   └─<font color="#A6E22E"><b>Done</b></font>. (0.000s)
    [...]
    │   │   ├─Calling <font color="#A1EFE4"><b>selftest_board_linux_bad_console</b></font> ...
    │   │   │   ├─<b>POWERON</b> (test)
    │   │   │   ├─<b>LINUX</b> (test-linux)
    │   │   │   ├─<b>POWEROFF</b> (test)
    │   │   │   └─<font color="#A6E22E"><b>Done</b></font>. (0.460s)
    │   │   ├─────────────────────────────────────────
    │   │   │ <font color="#A6E22E"><b>Success</b></font>: 17/17 tests passed
    │   │   └─<font color="#A6E22E"><b>Done</b></font>. (4.675s)
    │   └─<font color="#A6E22E"><b>Done</b></font>. (4.742s)
    ├─────────────────────────────────────────
    └─<font color="#A6E22E"><b>SUCCESS</b></font> (4.845s)</pre>

If you feel adventurous, there are even more selftests that check if the built-in testcases
work as intended:

.. html-console::

    <pre>bash-4.4$ tbot selftest_tc
    <font color="#F4BF75"><b>tbot</b></font> starting ...
    ├─Calling <font color="#A1EFE4"><b>selftest_tc</b></font> ...
    │   ├─Calling <font color="#A1EFE4"><b>testsuite</b></font> ...
    │   │   ├─Calling <font color="#A1EFE4"><b>selftest_tc_git_checkout</b></font> ...
    │   │   │   ├─Calling <font color="#A1EFE4"><b>git_prepare</b></font> ...
    │   │   │   │   ├─Setting up test repo ...
    │   │   │   │   ├─Calling <font color="#A1EFE4"><b>commit</b></font> ...
    │   │   │   │   │   └─<font color="#A6E22E"><b>Done</b></font>. (0.009s)
    │   │   │   │   ├─Creating test patch ...
    │   │   │   │   ├─Calling <font color="#A1EFE4"><b>commit</b></font> ...
    │   │   │   │   │   └─<font color="#A6E22E"><b>Done</b></font>. (0.004s)
    │   │   │   │   ├─Resetting repo ...
    │   │   │   │   └─<font color="#A6E22E"><b>Done</b></font>. (0.126s)
    │   │   │   ├─Cloning repo ...
    │   │   │   ├─Make repo dirty ...
    │   │   │   ├─Add dirty commit ...
    │   │   │   ├─Calling <font color="#A1EFE4"><b>commit</b></font> ...
    │   │   │   │   └─<font color="#A6E22E"><b>Done</b></font>. (0.004s)
    │   │   │   └─<font color="#A6E22E"><b>Done</b></font>. (0.321s)
    [...]
    │   │   ├─Calling <font color="#A1EFE4"><b>selftest_tc_build_toolchain</b></font> ...
    │   │   │   ├─Creating dummy toolchain ...
    │   │   │   ├─Attempt using it ...
    │   │   │   └─<font color="#A6E22E"><b>Done</b></font>. (0.153s)
    │   │   ├─────────────────────────────────────────
    │   │   │ <font color="#A6E22E"><b>Success</b></font>: 6/6 tests passed
    │   │   └─<font color="#A6E22E"><b>Done</b></font>. (3.679s)
    │   └─<font color="#A6E22E"><b>Done</b></font>. (3.764s)
    ├─────────────────────────────────────────
    └─<font color="#A6E22E"><b>SUCCESS</b></font> (3.894s)</pre>

tbot also allows you to run multiple testcases at once:

.. html-console::

    <pre>bash-4.4$ tbot selftest selftest_tc
    <font color="#F4BF75"><b>tbot</b></font> starting ...
    ├─Calling <font color="#A1EFE4"><b>selftest</b></font> ...
    │   ├─Calling <font color="#A1EFE4"><b>testsuite</b></font> ...
    [...]
    │   │   ├─────────────────────────────────────────
    │   │   │ <font color="#A6E22E"><b>Success</b></font>: 17/17 tests passed
    │   │   └─<font color="#A6E22E"><b>Done</b></font>. (4.788s)
    │   └─<font color="#A6E22E"><b>Done</b></font>. (4.873s)
    ├─Calling <font color="#A1EFE4"><b>selftest_tc</b></font> ...
    │   ├─Calling <font color="#A1EFE4"><b>testsuite</b></font> ...
    [...]
    │   │   ├─────────────────────────────────────────
    │   │   │ <font color="#A6E22E"><b>Success</b></font>: 6/6 tests passed
    │   │   └─<font color="#A6E22E"><b>Done</b></font>. (3.390s)
    │   └─<font color="#A6E22E"><b>Done</b></font>. (3.459s)
    ├─────────────────────────────────────────
    └─<font color="#A6E22E"><b>SUCCESS</b></font> (8.453s)</pre>

If you want an overview of the available testcases, use this command:

.. code-block:: shell-session

    $ tbot --list-testcases

----

The output you saw during the testcase runs was just a rough overview of what is going on.  That
might not be detailed enough for you.  By adding ``-v``, tbot will show all commands as they are
executed.  Add another one: ``-vv`` and you will also see command outputs!

.. html-console::

    <pre>bash-4.4$ tbot selftest_path_stat -vv
    <font color="#F4BF75"><b>tbot</b></font> starting ...
    ├─Calling <font color="#A1EFE4"><b>selftest_path_stat</b></font> ...
    │   ├─Setting up test files ...
    [...]
    │   ├─[<font color="#F4BF75">local</font>] test -S /tmp/tbot-wd/nonexistent
    │   ├─Checking stat results ...
    │   ├─[<font color="#F4BF75">local</font>] stat -t /dev
    │   │    ## /dev 4060 0 41ed 0 0 6 1025 20 0 0 1547723442 1547715500 1547715500 0 4096 system_u:object_r:device_t:s0
    [...]
    │   └─<font color="#A6E22E"><b>Done</b></font>. (0.145s)
    ├─────────────────────────────────────────
    └─<font color="#A6E22E"><b>SUCCESS</b></font> (0.278s)</pre>

.. note::
    There is one more verbosity level: ``-vvv``.  This is for debugging, if something doesn't quite work.
    It shows you all communication happening, both directions.  Try it if you want to, but be prepared:
    It will look quite messy!

One more commandline feature before we dive into python code:  If you are afraid of a destructive
command, you can run tbot with ``--interactive``:

.. html-console::

    <pre>bash-4.4$ tbot selftest_uname -vi
    <font color="#F4BF75"><b>tbot</b></font> starting ...
    ├─Calling <font color="#A1EFE4"><b>selftest_uname</b></font> ...
    │   ├─[<font color="#F4BF75">local</font>] uname -a
    <font color="#AE81FF">OK [Y/n]? </font>Y
    │   └─<font color="#A6E22E"><b>Done</b></font>. (2.721s)
    ├─────────────────────────────────────────
    └─<font color="#A6E22E"><b>SUCCESS</b></font> (2.848s)</pre>

Now tbot will kindly ask you before running each command!  (See? ``-emacs`` wouldn't answer as nicely!)

Testcases
---------
Ok, commandline isn't all that fun.  Let's dive deeper!  Some code please!

.. code-block:: python

    import tbot

    @tbot.testcase
    def hello_world():
        tbot.log.message("Hello World!")

This is tbot's hello world.  Stick this code into a file named ``tc.py``.  Now, if you check the list
of testcases (``tbot --list-testcases``), ``hello_world`` pops up.  Run it!

.. html-console::

    <pre>bash-4.4$ tbot hello_world
    <font color="#F4BF75"><b>tbot</b></font> starting ...
    ├─Calling <font color="#A1EFE4"><b>hello_world</b></font> ...
    │   ├─Hello World!
    │   └─<font color="#A6E22E"><b>Done</b></font>. (0.000s)
    ├─────────────────────────────────────────
    └─<font color="#A6E22E"><b>SUCCESS</b></font> (0.127s)</pre>

Hello tbot!

.. note::
    I am sure at least one person reading this will be offended by being told how to name their file.
    Why ``tc.py``?  I prefer calling it ``my_most_amazing_testcases.py``!

    Fear not, you can do just that!  You just need to tell tbot about it.  Instead of the above
    command, run:

    .. code-block:: shell-session

        $ tbot -t my_most_amazing_testcases.py hello_world

    You can also include all python files in a directory with ``-T``.

Well, before writing actual tests, I need to explain a few things:  In tbot, testcases are basically
python functions.  This means you can call them just like python functions!  From other testcases!
How about the following?

.. code-block:: python

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

1. Specifying a default value for the parameter:

   .. code-block:: python

    import tbot

    @tbot.testcase
    def greet(name: str = "World") -> None:
        tbot.log.message(f"Hello {name}!!")

2. Setting a value for the parameter!  That's right, you can set the parameter from the commandline.  It looks
   like this:

   .. html-console::

    <pre>bash-4.4$ tbot greet -p name=\&quot;tbot\&quot;
    <font color="#F4BF75"><b>tbot</b></font> starting ...
    ├─<b>Parameters:</b>
    │     name       = <font color="#F4BF75">&apos;tbot&apos;</font>
    ├─Calling <font color="#A1EFE4"><b>greet</b></font> ...
    │   ├─Hello tbot!!
    │   └─<font color="#A6E22E"><b>Done</b></font>. (0.000s)
    ├─────────────────────────────────────────
    └─<font color="#A6E22E"><b>SUCCESS</b></font> (0.238s)</pre>

   Note the escaped quotes around ``\"tbot\"``.  They are necessary because the value is `eval()`-uated
   internally.  This is done to allow you to set values of any type with ease.  Any python
   expression goes!  (Also evil ones, be careful ...)

As you'll see later on, there are cases where you should have default values and ones where
it doesn't make sense.  You'll have to decide individually ...

One more thing:  You'd expect a testcase to somehow be able to show whether it succeeded.  In tbot,
a testcase that returns normally passes and one that raises an ``Exception`` has failed.  This is
pretty convenient:  You can easily catch failures by using a try-block and your testcases will also
automatically fail if anything unexpected happens.

.. _quickstart_machines:

Machines
--------
Next up: Machines!  Machines are what tbot is made for.  Let's take a look at the diagram from the
landing page again:

.. only:: html

   .. image:: static/tbot.svg

.. only:: latex

   .. image:: static/tbot.png

Lab-host? It's a machine! Buildhost?  Just as well!  The boards you are testing?  You guessed it!

Let's start simple though:  Just run a command on the lab-host:

.. code-block:: python

    import tbot

    @tbot.testcase
    def greet_user() -> None:
        with tbot.acquire_lab() as lh:
            name = lh.exec0("id", "--user", "--name").strip()

            tbot.log.message(f"Hello {name}!")

Now try:

.. html-console::

    <pre>bash-4.4$ tbot greet_user -v
    <font color="#F4BF75"><b>tbot</b></font> starting ...
    ├─Calling <font color="#A1EFE4"><b>greet_user</b></font> ...
    │   ├─[<font color="#F4BF75">local</font>] id --user --name
    │   ├─Hello hws!
    │   └─<font color="#A6E22E"><b>Done</b></font>. (0.070s)
    ├─────────────────────────────────────────
    └─<font color="#A6E22E"><b>SUCCESS</b></font> (0.173s)</pre>

As you can see, tbot ran ``id --user --name`` to find your name.  You might be curious about the ``[local]``
part: That's the machine tbot ran the command on.  By default, the lab-host is your localhost. We'll
see later how to change that.

There are quite a few new things in the sample above.  Let's go through them one by one:

* :func:`tbot.acquire_lab`: This is a function provided by tbot that returns the selected lab-host.
* ``with tbot.acquire_lab() as lh:``: Each machine is a context manager.  To get access, you need
  to enter its context and as soon as you leave it the connection is destroyed.  If you haven't
  heard about context managers before, take a look at `Python with Context Managers
  <https://jeffknupp.com/blog/2016/03/07/python-with-context-managers/>`_.  They are really useful!
* :meth:`lh.exec0() <tbot.machine.linux.LinuxShell.exec0>`:  This is a function to run a command.
  Specifically **exec**-utes it and checks whether the return value is ``0``.  There are also others, for
  example, :meth:`lh.test() <tbot.machine.linux.LinuxShell.test>` which returns ``True`` if the command
  succeeded and ``False`` otherwise.
* All command executing methods take one parameter per commandline argument.  Each one will be properly
  escaped:  ``lh.exec0("echo", "!?#;>&<")`` would print ``!?#;>&<``, no manual quoting needed!
* :meth:`lh.exec0() <tbot.machine.linux.LinuxShell.exec0>` returns a string which I call ``.strip()``
  on.  The reason is that most commands include a trailing newline (``\n``).  I don't want that in the
  name so I remove it.

To learn more about the methods tbot provides for interacting with linux-machines, take a look at the
docs for :py:class:`~tbot.machine.linux.LinuxShell`.

One more feature I want to mention in this quick guide:  Most machines have an
:meth:`~tbot.machine.linux.LinuxShell.interactive` method.  This method will connect the
channel to the terminal and allows you to directly enter commands.  You can use it to make tbot
do some work, then do something manually.  Like a symbiotic development process.  It really makes
you a lot more productive if you embrace this idea!  There is also a testcase to call it from the
commandline:

.. html-console::

    <pre>bash-4.4$ tbot interactive_lab
    <font color="#F4BF75"><b>tbot</b></font> starting ...
    ├─Calling <font color="#A1EFE4"><b>interactive_lab</b></font> ...
    │   ├─Entering interactive shell ...

    <font color="#A1EFE4">local: </font><font color="#A6E22E">/tmp</font>&gt; whoami
    hws
    <font color="#A1EFE4">local: </font><font color="#A6E22E">/tmp</font>&gt; exit

    │   ├─Exiting interactive shell ...
    │   └─<font color="#A6E22E"><b>Done</b></font>. (49.746s)
    ├─────────────────────────────────────────
    └─<font color="#A6E22E"><b>SUCCESS</b></font> (49.851s)</pre>

Configuration
-------------
Up until now we did everything on our localhost.  That's boring!  tbot allows you to easily use a
lab-host that you can connect to via SSH for example.  To do that you have to write a small config
file.  There's a twist though!  The config file is actually a python module.  In this module, you
create a class for your lab-host.  If you have some special features on your lab-host you can add
them in there just as well!

The simplest config (for a lab-host connected via SSH) looks like this:

.. code-block:: python

    import tbot
    from tbot.machine import connector, linux

    class AwesomeLab(
        connector.ParamikoConnector,
        linux.Bash,
        linux.Lab,
    ):
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

.. code-block:: shell-session

    $ tbot -l <name-of-lab-config>.py interactive_lab

Congratulations! You now have a remote session on your lab-host!  You could also run some selftest to verify
that tbot can run these commands on your new lab-host as well:

.. html-console::

    <pre>bash-4.4$ tbot -l lab.py selftest_path_integrity -vv
    <font color="#F4BF75"><b>tbot</b></font> starting ...
    ├─Calling <font color="#A1EFE4"><b>selftest_path_integrity</b></font> ...
    │   ├─Logging in on <font color="#F4BF75">hws@78.79.32.85:22</font> ...
    │   ├─[<font color="#F4BF75">awesome-lab</font>] echo ${HOME}
    │   │    ## /home/hws
    │   ├─[<font color="#F4BF75">awesome-lab</font>] test -d /home/hws/tbot-workdir
    │   ├─[<font color="#F4BF75">awesome-lab</font>] mkdir -p /home/hws/tbot-workdir
    │   ├─Logging in on <font color="#F4BF75">hws@78.79.32.85:22</font> ...
    │   ├─[<font color="#F4BF75">awesome-lab</font>] mkdir -p /home/hws/tbot-workdir/folder
    │   ├─[<font color="#F4BF75">awesome-lab</font>] test -d /home/hws/tbot-workdir/folder
    │   ├─[<font color="#F4BF75">awesome-lab</font>] uname -a &gt;/home/hws/tbot-workdir/folder/file.txt
    │   ├─[<font color="#F4BF75">awesome-lab</font>] test -f /home/hws/tbot-workdir/folder/file.txt
    │   ├─[<font color="#F4BF75">awesome-lab</font>] rm -r /home/hws/tbot-workdir/folder
    │   ├─[<font color="#F4BF75">awesome-lab</font>] test -e /home/hws/tbot-workdir/folder/file.txt
    │   ├─[<font color="#F4BF75">awesome-lab</font>] test -e /home/hws/tbot-workdir/folder
    │   └─<font color="#A6E22E"><b>Done</b></font>. (2.833s)
    ├─────────────────────────────────────────
    └─<font color="#A6E22E"><b>SUCCESS</b></font> (2.959s)</pre>

As you can see, now it says ``[awesome-lab]`` in front of the commands.  tbot is running commands
remotely!

This was just a simple example ... Configs can get a lot bigger and a lot more complex.  Take a
look at the :ref:`configuration` documentation for more info!

Machine-Classes
---------------
When configuring the lab-host we already saw the definition of a machine class, but up to now I did
not really explain how those actually work.  Before we can dive into the next chapter, I have to
explain a bit about this:

tbot machines are classes which inherit from multiple components.  This allows easy mix and matching
to flexibly configure the machine for your needs.  There are two main components which every machine
needs and a number of mixins which allow further customization.  First the big ones:

1. **Connectors** define how a connection to the respective machine can be established.  The easiest
   way is the :py:class:`~tbot.machine.connector.SubprocessConnector` which just spawns a shell as a
   subprocess.  More complex examples include the :py:class:`~tbot.machine.connector.ParamikoConnector`
   which we saw above, or the :py:class:`~tbot.machine.connector.ConsoleConnector`.  For more
   in-depth documentation of the connectors, take a look at the :py:mod:`tbot.machine.connector`
   module.
2. **Shells** define the API for interacting with the machine.  This varies quite drastically
   between the different machine-types as shells behave differently.  Think how the U-Boot
   environment works completely different than the environment in Linux.  The lab-host config
   above used the :py:class:`~tbot.machine.linux.Bash` shell and we will see a
   :py:class:`~tbot.machine.board.UBootShell` in the next chapter.  For further details, go to the
   :py:mod:`tbot.machine.shell` module.

Between those two, sometimes you need a third part, a so-called **Initializer**.  An example for a
situation where one is needed would be this:  After opening the serial connection to your board, you
want to wait for the login-prompt first and enter your credentials before the shell is available.
For this, tbot provides a :py:class:`~tbot.machine.board.LinuxBootLogin` initializer.  If you have
multiple initializers in a machine-class, you need to keep in mind in which order they should run.

As a final part, there are some mixins for certain uses.  For example the
:py:class:`~tbot.machine.linux.Lab` mixin which marks a machine as a lab-host or the
:py:class:`~tbot.machine.linux.Builder` mixin which marks a machine as a build-host.  These can be
added whenever appropriate.

More details about machine-classes can be found in the :py:mod:`tbot.machine` module.

Hardware Interaction
--------------------
We haven't even talked to actual hardware yet!  Let's change that.  Unfortunately, as each device
is different, you'll have to figure out a few things yourself.

First Step:  Another config file.  The board needs to be configured in a second file.  Let's
start simple:

.. code-block:: python

    import tbot
    from tbot.machine import board, channel, connector, linux

    class SomeBoard(
        connector.ConsoleConnector,
        board.PowerControl,
        board.Board,
    ):
        name = "some-board"

        def poweron(self) -> None:
            """Procedure to turn power on."""

            # You can access the labhost as `self.host` (if you use the
            # ConsoleConnector).  In this case I have a simple command to
            # toggle power.
            self.host.exec0("remote_power", "bbb", "on")

            # If you can't automatically toggle power,
            # you have to insert some marker here that reminds you
            # to manually toggle power.  How about:
            tbot.log.message("Turn power on now!")

        def poweroff(self) -> None:
            """Procedure to turn power off."""
            self.host.exec0("remote_power", "bbb", "off")

        def connect(self, mach) -> channel.Channel:
            """Connect to the boards serial interface."""

            # `mach.open_channel` 'steals' mach's channel and runs the
            # given command to connect to the serial console.  Your command
            # should just connect its tty to the serial console like rlogin,
            # telnet, picocom or kermit do.  The minicom behavior will not work.
            return mach.open_channel("picocom", "-b", "115200", "bbb")

    # tbot will check for `BOARD`, don't forget to set it!
    BOARD = SomeBoard

If you did everything correctly, this should be enough to get a serial connection running.  Try this:

.. code-block:: shell-session

    $ tbot -l lab.py -b my-board.py interactive_board -vv

You should see the board starting to boot.  If not, go back and check manually if the commands by
themselves work.  You might also want to look at the :ref:`config-board` documentation.

Next up we will add config for the Linux running on the board (in the same file for now).  I'll skip
U-Boot in this quick guide for simplicity.  Here's the full new config:

.. code-block:: python

    import tbot
    from tbot.machine import board, connector, channel, linux

    class SomeBoard(
        connector.ConsoleConnector,
        board.PowerControl,
        board.Board,
    ):
        name = "some-board"

        def poweron(self) -> None:
            self.host.exec0("remote_power", "bbb", "on")

        def poweroff(self) -> None:
            self.host.exec0("remote_power", "bbb", "off")

        def connect(self, mach) -> channel.Channel:
            return mach.open_channel("picocom", "-b", "115200", "bbb")

    # Linux machine
    #
    # We use a config which boots directly to Linux without interaction
    # with a bootloader for this example.
    class SomeBoardLinux(
        board.Connector,
        board.LinuxBootLogin,
        linux.Bash,
    ):
        # Username for logging in once linux has booted
        username = "root"
        # Password.  If you don't need a password, set this to `None`
        password = "~ysu0dbi"

    BOARD = SomeBoard
    # You need to set `LINUX` now as well.
    LINUX = SomeBoardLinux

Again, adjust it as necessary.  If you are unsure about some parameters, you can check in the
``interactive_board`` session.  To learn more about the individual parameters, look at the
:ref:`config-board` and :ref:`config-board-linux-standalone` docs.

If you set everything correctly, you should be able to run:

.. code-block:: shell-session

    $ tbot -l lab.py -b my-board.py interactive_linux -vv

You now have a shell on the board!  As before, you can also try running a selftest:

.. code-block:: shell-session

    $ tbot -l lab.py -b my-board.py selftest_board_linux -vv

.. html-console::

    <pre>bash-4.4$ tbot -l lab.py -b my-board.py selftest_board_linux -vv
    <font color="#F4BF75"><b>tbot</b></font> starting ...
    ├─Calling <font color="#A1EFE4"><b>selftest_board_linux</b></font> ...
    │   ├─Logging in on <font color="#F4BF75">hws@78.79.32.85:22</font> ...
    │   ├─[<font color="#F4BF75">awesome-lab</font>] connect bbb
    │   ├─[<font color="#F4BF75">awesome-lab</font>] remote_power bbb -l
    │   │    ## bbb         	off
    │   ├─<b>POWERON</b> (bbb)
    │   ├─[<font color="#F4BF75">awesome-lab</font>] remote_power bbb on
    │   │    ## Power on   bbb: OK
    │   ├─<b>UBOOT</b> (bbb-uboot)
    │   │    &lt;&gt;
    │   │    &lt;&gt; U-Boot 2018.11-00191-gd73d81fd85 (Nov 20 2018 - 06:01:01 +0100)
    │   │    &lt;&gt;
    │   │    &lt;&gt; CPU  : AM335X-GP rev 2.1
    │   │    &lt;&gt; Model: TI AM335x BeagleBone Black
    │   │    &lt;&gt; DRAM:  512 MiB
    │   │    &lt;&gt; NAND:  0 MiB
    │   │    &lt;&gt; MMC:   OMAP SD/MMC: 0, OMAP SD/MMC: 1
    │   │    &lt;&gt; Loading Environment from FAT... ** No partition table - mmc 0 **
    │   │    &lt;&gt; No USB device found
    │   │    &lt;&gt; &lt;ethaddr&gt; not set. Validating first E-fuse MAC
    │   │    &lt;&gt; Net:   eth0: ethernet@4a100000
    │   ├─<b>LINUX</b> (bbb-linux)
    │   ├─[<font color="#F4BF75">bbb-uboot</font>] setenv serverip 192.168.1.1
    │   ├─[<font color="#F4BF75">bbb-uboot</font>] setenv netmask 255.255.255.0
    │   ├─[<font color="#F4BF75">bbb-uboot</font>] setenv ipaddr 192.168.1.10
    │   ├─[<font color="#F4BF75">bbb-uboot</font>] mw 0x81000000 0 0x4000
    │   ├─[<font color="#F4BF75">bbb-uboot</font>] setenv rootpath /opt/core-image-lsb-sdk-generic-armv7a-hf
    │   ├─[<font color="#F4BF75">bbb-uboot</font>] run netnfsboot
    │   │    &lt;&gt; Booting from network ... with nfsargs ...
    │   │    &lt;&gt; link up on port 0, speed 100, full duplex
    │   │    &lt;&gt; TFTP from server 192.168.1.1; our IP address is 192.168.1.10
    │   │    &lt;&gt; Load address: 0x82000000
    │   │    &lt;&gt; Loading: #################################################################
    │   │    &lt;&gt; 	 ########################
    │   │    &lt;&gt; 	 2.9 MiB/s
    │   │    &lt;&gt; done
    │   │    &lt;&gt; Bytes transferred = 9883000 (96cd78 hex)
    │   │    &lt;&gt; link up on port 0, speed 100, full duplex
    │   │    &lt;&gt; TFTP from server 192.168.1.1; our IP address is 192.168.1.10
    │   │    &lt;&gt; Load address: 0x88000000
    │   │    &lt;&gt; Loading: #####
    │   │    &lt;&gt; 	 1.1 MiB/s
    │   │    &lt;&gt; done
    │   │    &lt;&gt; Bytes transferred = 64051 (fa33 hex)
    │   │    &lt;&gt; ## Flattened Device Tree blob at 88000000
    │   │    &lt;&gt;    Booting using the fdt blob at 0x88000000
    │   │    &lt;&gt;    Loading Device Tree to 8ffed000, end 8ffffa32 ... OK
    │   │    &lt;&gt;
    │   │    &lt;&gt; Starting kernel ...
    │   │    &lt;&gt;
    │   │    &lt;&gt; [    0.000000] Booting Linux on physical CPU 0x0
    │   │    &lt;&gt; [    0.000000] Linux version 4.9.126 (build@denx) (gcc version 7.2.1 20171011 (Linaro GCC 7.2-2017.11) ) #1 SMP PREEMPT Wed Dec 12 03:12:29 CET 2018
    │   │    &lt;&gt; [    0.000000] CPU: ARMv7 Processor [413fc082] revision 2 (ARMv7), cr=10c5387d
    │   │    &lt;&gt; [    0.000000] CPU: PIPT / VIPT nonaliasing data cache, VIPT aliasing instruction cache                                              Hello there ;)
    │   │    &lt;&gt; [    0.000000] OF: fdt:Machine model: TI AM335x BeagleBone Black
    │   │    &lt;&gt; [    0.000000] efi: Getting EFI parameters from FDT:
    │   │    &lt;&gt; [    0.000000] efi: UEFI not found.
    │   │    &lt;&gt; [    0.000000] cma: Reserved 48 MiB at 0x9c800000
    [...]
    │   │    &lt;&gt; Poky (Yocto Project Reference Distro) 2.4 generic-armv7a-hf /dev/ttyS0
    │   │    &lt;&gt;
    │   │    &lt;&gt; generic-armv7a-hf login: root
    │   ├─Calling <font color="#A1EFE4"><b>selftest_machine_shell</b></font> ...
    │   │   ├─Testing command output ...
    │   │   ├─[<font color="#F4BF75">bbb-linux</font>] echo &apos;Hello World&apos;
    │   │   │    ## Hello World
    │   │   ├─[<font color="#F4BF75">bbb-linux</font>] echo &apos;$?&apos; &apos;!#&apos;
    │   │   │    ## $? !#
    [...]
    │   │   └─<font color="#A6E22E"><b>Done</b></font>. (3.355s)
    │   ├─<b>POWEROFF</b> (bbb)
    │   ├─[<font color="#F4BF75">pollux</font>] remote_power bbb off
    │   │    ## Power off  bbb: OK
    │   └─<font color="#A6E22E"><b>Done</b></font>. (44.150s)
    ├─────────────────────────────────────────
    └─<font color="#A6E22E"><b>SUCCESS</b></font> (44.624s)</pre>

Hardware Use from Tests
-----------------------
Last part of this guide will be interacting with the board from a testcase.  It's pretty straight
forward:

.. code-block:: python

    import tbot

    @tbot.testcase
    def test_board() -> None:
        # Get access to the lab-host as before
        with tbot.acquire_lab() as lh:
            # This context is for the "hardware".  Once you enter
            # it, the board will be powered on and as soon as
            # you exit it, it will be turned off again.
            with tbot.acquire_board(lh) as b:
                # This is the context for the "Linux machine".
                # Entering it means tbot will listen to the
                # board booting and give you a machine handle
                # as soon as the shell is available.
                with tbot.acquire_linux(b) as lnx:
                    lnx.exec0("uname", "-a")

Those two additional indentation levels aren't nice - We can refactor the code to
look like this (I showed the explicit version first so you can see what is going on):

.. code-block:: python

    import tbot

    @tbot.testcase
    def test_board() -> None:
        with  tbot.acquire_lab() as lh,
              tbot.acquire_board(lh) as b,
              tbot.acquire_linux(b) as lnx:
            lnx.exec0("uname", "-a")

There is still one issue with this design:  Let's pretend this is a test to check some
board functionality.  Maybe you have quite a few testcases that each check different
parts.  Now, we want to call all of them from some "master" test, so we can test everything
at once.

The issue we will run into is that each testcase will A) reconnect to the lab-host and
B) powercycle the board.  This will be very very slow!  We can do better!

The idea is that testcases take the lab and board as optional parameters.  This allows
reusing the old connection and won't powercycle the board for each test (if you need powercycling,
you can of course do it like above).  To make this as easy as possible, tbot provides the
:py:func:`with_linux` decorator.  You can use it like this:

.. code-block:: python

    import typing
    import tbot
    from tbot.machine import linux, board

    @tbot.testcase
    @tbot.with_linux
    def test_board(
        lnx: linux.LinuxShell,
        param: str = "-a",
    ) -> None:
        lnx.exec0("uname", param)

    @tbot.testcase
    def call_it() -> None:
        with tbot.acquire_lab() as lh:
            test_board(lh, "-r")

    @tbot.testcase
    def call_it_prepared() -> None:
        with tbot.acquire_lab() as lh,
             tbot.acquire_board(lh) as b,
             tbot.acquire_linux(b) as lnx:
            test_board(lnx, "-n")

You can still call ``test_board`` from the commandline, but ``call_it`` and ``call_it_prepared``
work as well!

There is also :py:func:`with_lab` and :py:func:`with_uboot` for those two usecases.

That's it for the quick-start guide.  If you want to dive deeper, you might want to follow these
links:

* :py:mod:`tbot.machine` - More machine documentation
* :ref:`configuration` - Detailed docs about configuration
* :py:mod:`tbot.tc` - Builtin testcases for a variety of jobs
