.. _recipes:

Recipes
=======
To make writing testcases as productive as possible, this page contains a number of examples which
you can quickly copy and adapt to get your tests up and running.  These are:

#. Most common:

   - :ref:`recipe-lab`
   - :ref:`recipe-uboot`
   - :ref:`recipe-linux`

#. For board tests

   - :ref:`recipe-powercycling`
   - :ref:`recipe-soft-reset`

#. For lab & general

   - :ref:`recipe-copy`

.. _recipe-lab:

Testcase on lab-host
--------------------
A testcase that interacts with the lab should be able to take the LabHost
as a parameter, so it won't open a parallel connection each time.  For easily
writing such testcases, tbot has the :func:`tbot.with_lab` decorator:

.. code-block:: python

   import tbot
   from tbot.machine import linux

   @tbot.testcase
   @tbot.with_lab
   def testcase_with_lab(lh: linux.LinuxShell) -> None:
       lh.exec0("uname", "-a")

The decorator is syntactic sugar for acquiring the default selected lab-host
if none was supplied as the first parameter.

.. _recipe-uboot:

Testcase with U-Boot
--------------------
A testcase that interacts with U-Boot should be able to take the U-Boot
machine as a paramter as long as it does not require the board to powercycle,
etc.  Similar to the :func:`tbot.with_lab` decorater, there is :func:`tbot.with_uboot`,
which will initialize the selected Board if no active U-Boot machine was given
as a parameter:

.. code-block:: python

   import tbot
   from tbot.machine import board

   @tbot.testcase
   @tbot.with_uboot
   def testcase_with_uboot(ub: board.UBootShell) -> None:
       ub.exec0("version")


.. _recipe-linux:

Testcase with Linux (on the board)
----------------------------------
A testcase that is supposed to be run on the boards linux should be able
to take the board Linux machine as a paramter as long as it does not require
powercycling, etc.  Again, there is a decorator: :func:`tbot.with_linux`

.. code-block:: python

   import tbot
   from tbot.machine import board

   @tbot.testcase
   @tbot.with_linux
   def testcase_with_linux(lnx: board.LinuxMachine) -> None:
       lnx.exec0("uname", "-a")


.. _recipe-powercycling:

Powercycling the Board
----------------------
If a testcase requires powercycling, you should write your testcase like this:

.. code-block:: python

   import tbot
   from tbot.machine import linux

   @tbot.testcase
   @tbot.with_lab
   def testcase_with_lab(lh: linux.LinuxShell) -> None:
       with tbot.acquire_board(lh) as b,
            tbot.acquire_linux(b) as lnx:
           # First boot, do things
           ...

       # Powercycling now ...

       with tbot.acquire_board(lh) as b,
            tbot.acquire_linux(b) as lnx:
           # Second boot, do things
           ...


.. _recipe-soft-reset:

(Soft-)Resetting with ``bmode`` or ``reset``
-------------------------------------
In some tests, you might need to use ``bmode`` or ``reset`` to trigger a soft-reset without turning
off power.  For these, you'll want to use the following recipe:

.. code-block:: python

   with tbot.acquire_board(lh) as b:
       with tbot.acquire_uboot(b) as ub:
          # Board is ready now, set everything up
          ...

          # Call bmode with ub.boot().  This will grant us the board's channel
          # which we can now give to a new U-Boot machine
          ch = ub.boot("bmode", "emmc")

       # Restart U-Boot, this time giving it the channel from ub.boot()
       with tbot.acquire_uboot(ch) as ub:
          ub.exec0("version")


.. _recipe-copy:

Copy files from one machine to another
--------------------------------------
This is a very common use-case so tbot provides a builtin testcase for it:
:func:`tbot.tc.shell.copy`.  Use it like this:

.. code-block:: python

   from tbot.tc import shell

   # Copy a file from the selected lab-host to localhost
   with tbot.acquire_lab() as lh,
        tbot.acquire_local() as lo:

       file_on_labhost = lh.fsroot / "etc" / "shadow"
       file_on_localhost = lh.workdir / "sneaky_stolen_passwords"

       shell.copy(file_on_labhost, file_on_localhost)
