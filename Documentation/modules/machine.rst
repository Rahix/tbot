.. py:module:: tbot.machine

``tbot.machine``
================
Machines are tbot's abstraction over the different computers it can interact
with.  This includes the machine it is running on
(:py:class:`~tbot.selectable.LocalLabHost`), the lab-host
(:py:class:`~tbot.selectable.LabHost`), the device-under-test, as U-Boot
(:py:class:`~tbot.selectable.UBootMachine`) and as Linux
(:py:class:`~tbot.selectable.LinuxMachine`).  Machines are composed of three
different parts:

1. The :py:class:`~tbot.machine.connector.Connector` which is responsible for
   establishing a connection to the machine.  This can happen in many different
   ways, for example using Paramiko, by opening a serial-console, etc...
2. Optionally, any number of :py:class:`~tbot.machine.Initializer` s.  These
   can, step by step, setup the channel into a state until the shell appears.
   Examples would be the :py:class:`~tbot.machine.board.UBootAutobootIntercept`
   (catch the autoboot prompt and press a key) or the
   :py:class:`~tbot.machine.board.LinuxBootLogin` (wait for the login prompt
   and then enter username & password).
3. The :py:class:`~tbot.machine.shell.Shell` which defines how a testcase can
   interact with this machine.  Typically this is an interface of methods for
   running commands.

Composition is done using multiple-inheritance, like this:

.. code-block:: python

   from tbot.machine import connector, linux

   def MyLabHost(
       # The connector:
       connector.ParamikoConnector,

       # - No initializers here -

       # The shell:
       linux.Bash,
   ):
       # Options for the paramiko connector:
       hostname = "78.79.32.85"
       username = "tbot-user"

       # We can override anything we like to customize it
       @property
       def workdir(self):
           return linux.Workdir.static(self, "/opt/tbot-{self.username}")

Machines are used as context-managers.  This means you will later on
instanciate the above machine like this (if you were to hardcode the machine.
You should probably use tbot's :ref:`configuration` mechanism instead):

.. code-block:: python

   @tbot.testcase
   def footest():
       with MyLabHost() as lh:
           # Run a command:
           lh.exec0("uname", "-a")

For more information about the individual parts of a machine, take a look at
:py:mod:`tbot.machine.connector`, :py:class:`tbot.machine.Initializer`, and
:py:mod:`tbot.machine.shell`.  Specifically for interacting with Linux
machines, you should head over to :ref:`linux-shells`.

Base-Class
----------
.. autoclass:: tbot.machine.Machine
   :members:

Initializers
------------
.. autoclass:: tbot.machine.Initializer
   :members:
   :private-members:
