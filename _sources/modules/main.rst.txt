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

Testcase Skipping
-----------------
Sometimes a test can only run with certain prerequisites met.  You can write a
testcase to automatically skip when they aren't, using :func:`tbot.skip`:

.. autofunction:: tbot.skip
.. autoclass:: tbot.SkipException

Deprecated items
----------------

Convenience Decorators
^^^^^^^^^^^^^^^^^^^^^^
.. autofunction:: tbot.with_lab
.. autofunction:: tbot.with_uboot
.. autofunction:: tbot.with_linux

Default Machine Access
^^^^^^^^^^^^^^^^^^^^^^
.. autofunction:: tbot.acquire_lab
.. autofunction:: tbot.acquire_local
.. autofunction:: tbot.acquire_board
.. autofunction:: tbot.acquire_uboot
.. autofunction:: tbot.acquire_linux
