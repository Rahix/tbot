.. py:module:: tbot

``tbot``
========

Testcase Decorators
-------------------
In tbot, testcases are marked using one of the following decorators.  This will
make tbot aware of the testcase and allows you to call it from the commandline.
The testcase decorators will also track time and success of each run.

.. autofunction:: tbot.testcase
.. autofunction:: tbot.named_testcase

Context
-------
The new mechanism for machine management is the :ref:`context <context>`
(superseding :py:mod:`tbot.selectable`).  The global context is stored in
:py:data:`tbot.ctx` which is an instance of :py:class:`tbot.Context`.  Read the
:ref:`context` guide for a detailed introduction.

.. py:data:: tbot.ctx
   :type: tbot.Context

   The global context.  This context should be used in testcases for accessing
   machines via the following pattern:

   **Single Machine**:

   .. code-block:: python

      @tbot.testcase
      def test_with_labhost():
          with tbot.ctx.request(tbot.role.LabHost) as lh:
              lh.exec0("uname", "-a")

   **Multiple Machines**:

   .. code-block:: python

      @tbot.testcase
      def test_with_board_and_lab():
         with tbot.ctx() as cx:
            lh = cx.request(tbot.role.LabHost)
            lnx = cx.request(tbot.role.BoardLinux)

            lh.exec0("hostname")
            lnx.exec0("hostname")

   See the :py:class:`tbot.Context` class below for the API details.

.. autoclass:: tbot.Context
   :members:

Convenience Decorators
----------------------
To make writing testcase interacting with machines easier, tbot provides three
more decorators to allow easily writing extensible testcases.  They look like
this:

.. code-block:: python

   import tbot
   from tbot.machine import board

   @tbot.testcase
   @tbot.with_uboot
   def uboot_testcase(ub: board.UBootShell, foo: bool = False):
      ub.exec0("version")

``uboot_testcase()`` can now be called in three different ways:

#. Without any arguments (eg. from the commandline):  The decorator will take
   care of first connecting to the lab-host and then powering up the board and
   initializing the U-Boot machine.
#. Passing a lab-host as an argument:  The decorator will take care of powering
   up the board and initializing the U-Boot machine.
#. Passing a U-Boot machine: No additional work is needed and the test can run
   immediately.

.. note::

   As seen above, you can still have additional arguments as well.  Those will
   work as expected, but you need to pass them as kwargs now:

   .. code-block:: python

      uboot_testcase(foo=True)
      uboot_testcase(lh, foo=True)
      uboot_testcase(ub, foo=True)

   Or on the commandline:

   .. code-block:: shell-session

      $ tbot @myargs uboot_testcase -pfoo=True

Three decorators of this style are currently available:

- :func:`tbot.with_lab`
- :func:`tbot.with_uboot`
- :func:`tbot.with_linux`

.. autofunction:: tbot.with_lab
.. autofunction:: tbot.with_uboot
.. autofunction:: tbot.with_linux

Testcase Skipping
-----------------
Sometimes a test can only run with certain prerequisites met.  You can write a
testcase to automatically skip when they aren't, using :func:`tbot.skip`:

.. autofunction:: tbot.skip
.. autoclass:: tbot.SkipException

Default Machine Access
----------------------
There are a few machines which can be configured in the *Configuration* and
then accessed through the following functions.  This allows you to write
generic testcases, based on using one or more of them:

.. autofunction:: tbot.acquire_lab
.. autofunction:: tbot.acquire_local
.. autofunction:: tbot.acquire_board
.. autofunction:: tbot.acquire_uboot
.. autofunction:: tbot.acquire_linux
