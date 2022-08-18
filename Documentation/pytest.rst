pytest Integration
==================
For building a large testsuite, it makes sense to leverage existing frameworks
for driving the tests and generating reports.  One popular framework for Python
is `pytest <https://pytest.org/>`_.  This guide shows how you can use tbot to
run hardware tests in pytest:

General Concept
---------------
The idea is to make the tbot context available as a fixture to pytest
testcases.  These can then request machines as they need to interact with the
hardware.

To not make the test-runs excruciatingly slow, machines should be "kept alive"
between individual tests.  This means, for example, that the board should not
be powered off after each test just for the next test to power it on again.

There is challenge here, though:  When a test fails, the board probably
*should* be powercycled anyway, to make sure the following test will not be
affected by the previous test failure.

tbot's :py:class:`tbot.Context` has a mechanism to allow implementing exactly
that.  You will see how it works below:

``conftest.py``
---------------
``conftest.py`` is pytest's configuration file.  We need to define a fixture
for tbot's context here.  We also need to provide a mechanism to allow
selecting the tbot configuration.  This can be done by adding custom
command-line parameters.  All in all, this is a good skeleton to start from:

.. code-block:: python

   import pytest
   import tbot
   from tbot import newbot

   def pytest_addoption(parser, pluginmanager):
       parser.addoption("--tbot-config", action="append", default=[], dest="tbot_configs")
       parser.addoption("--tbot-flag", action="append", default=[], dest="tbot_flags")

   @pytest.fixture(scope="session", autouse=True)
   def tbot_ctx(pytestconfig):
       # Only register configuration when nobody else did so already.
       if not tbot.ctx.is_active():
           # Register flags
           for flag in pytestconfig.option.tbot_flags:
               tbot.flags.add(flag)

           # Register configuration
           for config in pytestconfig.option.tbot_configs:
               newbot.load_config(config, tbot.ctx)

       with tbot.ctx:
           # Configure the context for keep_alive (so machines can be reused
           # between tests).  reset_on_error_by_default will make sure test
           # failures lead to a powercycle of the DUT anyway.
           with tbot.ctx.reconfigure(keep_alive=True, reset_on_error_by_default=True):
               # Tweak the standard output logging options
               with tbot.log.with_verbosity(tbot.log.Verbosity.STDOUT, nesting=1):
                   yield tbot.ctx

Testcases
---------
After writing the pytest config, you can start writing testcases.  You should
probably read the `pytest Getting Started
<https://docs.pytest.org/en/7.1.x/getting-started.html>`_ guide first if you
are not familiar with pytest.

Testcases can just use ``tbot.ctx`` like usual as the fixture will be activated
automatically (due to ``autouse=True``).  Here is an example:

.. code-block:: python

   # test_examples.py
   import tbot

   def test_encabulator():
       with tbot.ctx.request(tbot.role.BoardLinux) as lnx:
           lnx.exec0("systemctl", "status", "turbo-encabulator.service")

Now you are ready to run it!  You have to translate your ``newbot`` commandline
parameters to ``pytest`` like this:

.. code-block:: shell-session

   $ # This newbot commandline...
   $ newbot -c config.my_lab -c config.board1 -f foo ...
   $ # becomes this pytest commandline:
   $ pytest --tbot-config config.my_lab --tbot-config config.board1 --tbot-flag foo ...

You can call pytest with ``-vs`` to see the tbot logging output during the
tests.

``keep_alive`` Notes
--------------------
As mentioned above, we use the ``keep_alive`` context mode to speed up the
test-run.  This comes with a number of gotchas, though.  You need to design
your testcases accordingly so the ``keep_alive`` mode does not lead to
problems.

- A testcase must leave all machines in the same state that it found them in.
  If this is not possible, for example when running a crash test, the relevant
  machines should be requested with ``exclusive=True`` to make sure the machine
  is powercycled before the next testcase accesses it.

- Testcases by default must assume that the machine was already active before
  they got it.  If this is not wanted, the relevant machines should be
  requested with ``reset=True`` to enforce a powercycle before the testcase
  accesses the machine.

- If some machines may prevent requesting some other machine (like
  ``BoardLinux`` prevents ``BoardUBoot``), testcases requiring the prevented
  one should use :py:meth:`~tbot.Context.teardown_if_alive` to deactivate the
  offending machine first.

Here are a few examples of such testcases:

.. code-block:: python

   import time
   import tbot
   from tbot.machine import linux

   def test_watchdog_timeout():
       with tbot.ctx.request(tbot.role.BoardLinux, exclusive=True) as lnx:
           wdt = lnx.fsroot / "dev" / "watchdog0"
           lnx.exec0("echo", "1", linux.RedirStdout(wdt))

           # And now we expect the U-Boot header within 60 seconds
           ch = lnx.ch.take()
           with tbot.log.EventIO(
               ["board", "wdt-timeout"],
               tbot.log.c("Waiting for the watchdog reset... ").bold,
               verbosity=tbot.log.Verbosity.QUIET,
           ) as ev, ch.with_stream(ev):
               ev.verbosity = tbot.log.Verbosity.STDOUT
               ev.prefix = "   <> "
               ch.expect("U-Boot 2022.", timeout=60)

   def test_uboot_can_echo():
       tbot.ctx.teardown_if_alive(tbot.role.BoardLinux)

       with tbot.ctx.request(tbot.role.BoardUBoot) as ub:
           ub.exec0("echo", "Hello World")
