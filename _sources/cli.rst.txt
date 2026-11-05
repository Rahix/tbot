.. _cli:

tbot CLI
========
tbot is, for the most part, a library to interact with embedded devices and
automate working with them.  But it also ships with a CLI (commandline
interface) tool which ties together code using tbot.  Usage of this CLI is not
at all mandatory, you can write your own scripts just as well.  But the common
interface has proven to be quite useful for larger projects.

Advantages of using tbot's CLI are:

- Automatic configuration
- Easy mechanism to modularize configuration
- Common command to call many different testcases
- Provides commandline flags for common tbot debugging needs
- Pretty output!

.. note::

   The new CLI is called ``newbot`` and this is what will be described in this
   document.  There is also an old tool called ``tbot`` which will be
   deprecated in a future release.

Usage
-----
A gentle introduction can be found in the :ref:`quickstart` guide.  This
document here serves as a reference documentation.

.. code-block:: text

   usage: tbot [options] [testcases ...]

   positional arguments:
     testcase              testcases that should be run.

   options:
     -h, --help            show this help message and exit
     -C WORKDIR            use WORKDIR as working directory instead of the current directory.
     -c CONFIG, --config CONFIG
     -f FLAG               set a user defined flag to change testcase behaviour
     -k, --keep-alive      keep machines alive for later tests to reacquire them
     -v                    increase the verbosity
     -q                    decrease the verbosity
     --version             show program's version number and exit

Testcases and configuration are specified as Python module paths.  For
testcases, the last element is the testcase function to be called.
Configuration modules are expected to contain a ``register_machines()``
function which will be called to enable the config.  This can be expressed in
some simple equivalent Python code.  Calling

.. code-block:: shell-session

   $ newbot -c config.my_config tc.examples.foo tc.interactive.linux

would, in simple terms, be equivalent to this:

.. code-block:: python

   # 1. load and enable config
   import config.my_config
   config.my_config.register_machines(tbot.ctx)

   # 2. run first testcase
   import tc.examples
   tc.examples.foo()

   # 3. run second testcase
   import tc.interactive
   tc.interactive.linux()

.. _cli-flags:

``-f`` Flags
------------
Flags are a mechanism to allow quickly switching settings in configuration or
testcases.  For example, a flag might be used to switch to booting from a
different source.

All flags passed to ``newbot`` with ``-f`` are added to the
:py:data:`tbot.flags` set.  Config and testcases can then check for them like
this:

.. code-block:: python

   # Check if flag is present
   if "boot-nfs" in tbot.flags:
       bootargs = "root=/dev/nfs nfsroot=...,tcp,v3"
   else:
       bootargs = "root=/dev/mmcblk0p1"

   # Check if flag is absent
   if "silent-boot" not in tbot.flags:
       bootargs += " loglevel=7"

   uboot.env("bootargs", bootargs)

``-k`` Keep Alive
-----------------
By default, machine instances are "torn down" as soon as the outermost
with-block which requested them ends.  This means, that in the following code,
the board is rebooted between the two blocks:

.. code-block:: python

   with tbot.ctx.request(tbot.role.BoardLinux) as lnx:
       lnx.exec0("echo", "first boot")

   with tbot.ctx.request(tbot.role.BoardLinux) as lnx:
       lnx.exec0("echo", "second boot")

However, this is often not ideal because it leads to excessively long testcase
run times.  The ``-k`` flag instead changes behaviour such that an instance is
"kept alive" until the very end of a ``newbot`` run.  Thus, the board would not
reboot in the above example.

To make testcases which require a powercycle still work, they should explicitly
request a reset.  This way, it will work both with and without ``-k``.

.. code-block:: python

   with tbot.ctx.request(tbot.role.BoardLinux) as lnx:
       lnx.exec0("echo", "first boot")

   with tbot.ctx.request(tbot.role.BoardLinux, reset=True) as lnx:
       lnx.exec0("echo", "second boot")


You can read more about this in the :ref:`context` documentation.

``-v`` Verbose
--------------
Verbose mode can be used to debug problems in lower layers of the
communication.  It shows all sent and received data on all "channels".  For
example, when tbot doesn't seem to recognize a login-prompt, this can help.

Migrating to ``newbot``
-----------------------
If you have previously written tbot code for the old ``tbot`` CLI tool, this
section details how to migrate to ``newbot``.  Before starting here, please
adjust your code for the :ref:`context` API as detailed in
:ref:`context_migration`.  ``newbot`` no longer supports the legacy style
configuration.

From there, everything should be quite straight forward.  The only thing which changes is the commandline syntax:

- The ``-l`` and ``-b`` config arguments have been consolidated into a single
  ``-c`` flag.  Instead of paths, you now need to specify Python modules.  So
  ``-l configs/my_lab.py`` becomes ``-c configs.my_lab``.

- Testcases are no longer "collected" from directories, they are now also
  imported using standard Python imports.  A testcase called
  ``test_uboot_emmc`` in a file ``tc/uboot/tests.py`` will now be called as
  ``tc.uboot.tests.test_uboot_emmc``.

  As this can get quite cumbersome to type, it is often a good idea to
  re-import testcases in a higher level module.  For example you could add this
  line to ``tc/__init__.py``:

  .. code-block:: python

     from .uboot.tests import test_uboot_emmc

  And then call the testcase as ``tc.test_uboot_emmc``.
