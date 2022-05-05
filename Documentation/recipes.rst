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

#. For lab & general

   - :ref:`recipe-copy`

.. _recipe-lab:

Testcase on lab-host
--------------------
.. code-block:: python

   import tbot

   @tbot.testcase
   def testcase_with_lab() -> None:
       with tbot.ctx.request(tbot.role.LabHost) as lh:
           lh.exec0("uname", "-a")

.. _recipe-uboot:

Testcase with U-Boot
--------------------
.. code-block:: python

   import tbot

   @tbot.testcase
   def testcase_with_uboot() -> None:
       # This is not strictly needed but it will automatically powercycle the
       # board if it was previously in Linux.
       tbot.ctx.teardown_if_alive(tbot.role.BoardLinux)

       with tbot.ctx.request(tbot.role.BoardUBoot) as lh:
           ub.exec0("version")

.. _recipe-linux:

Testcase with Linux (on the board)
----------------------------------
.. code-block:: python

   import tbot

   @tbot.testcase
   def testcase_with_linux() -> None:
       with tbot.ctx.request(tbot.role.BoardLinux) as lnx:
           lnx.exec0("uname", "-a")


.. _recipe-powercycling:

Powercycling the Board
----------------------
If a testcase requires powercycling, you should write your testcase like this:

.. code-block:: python

   import tbot
   from tbot.machine import linux

   @tbot.testcase
   def testcase_powercycle() -> None:
       with tbot.ctx.request(tbot.role.BoardLinux) as lnx:
           lnx.exec0("touch", "/tmp/this-is-a-volatile-file")

       # the reset=True will make sure to trigger a powercycle
       with tbot.ctx.request(tbot.role.BoardLinux, reset=True) as lnx:
           assert not lnx.test("test", "-e", "/tmp/this-is-a-volatile-file")

.. _recipe-copy:

Copy files from one machine to another
--------------------------------------
This is a very common use-case so tbot provides a builtin testcase for it:
:func:`tbot.tc.shell.copy`.  Use it like this:

.. code-block:: python

   from tbot.tc import shell

   # Copy a file from the selected lab-host to localhost
   with tbot.ctx() as cx:
       lo = cx.request(tbot.role.LocalHost)
       lh = cx.request(tbot.role.LabHost)

       file_on_labhost = lh.fsroot / "etc" / "shadow"
       file_on_localhost = lo.workdir / "sneaky_stolen_passwords"

       shell.copy(file_on_labhost, file_on_localhost)
