.. py:module:: tbot.machine.connector

``tbot.machine.connector``
==========================
Connectors are one of the three parts of a machine:  The connector is
responsible for establishing the initial channel for a machine.  This can work
in many different ways, either a simple subprocess, an ssh-connection, a
serial-console device, or a telnet session.

All connectors should inherit from the
:py:class:`~tbot.machine.connector.Connector` base-class.

Provided Connectors
-------------------
For a lot of commonly used cases, tbot already has connectors at hand.  These
are:

Subprocess
~~~~~~~~~~
.. autoclass:: tbot.machine.connector.SubprocessConnector
   :members:

Paramiko
~~~~~~~~
.. autoclass:: tbot.machine.connector.ParamikoConnector
   :members:

Serial Console
~~~~~~~~~~~~~~
.. autoclass:: tbot.machine.connector.ConsoleConnector
   :members:

Plain SSH
~~~~~~~~~
.. autoclass:: tbot.machine.connector.SSHConnector
   :members:
   :undoc-members:

Base-Class
----------

.. autoclass:: tbot.machine.connector.Connector
   :members:
   :private-members:
