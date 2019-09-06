.. py:module:: tbot

``tbot``
========

Testcase Decorators
-------------------
In tbot, testcases are marked using one of the following decorators.  This will make tbot aware of the testcase and allows you to call it from the commandline.  The testcase decorators will also track time and success of each run.

.. autofunction:: tbot.testcase
.. autofunction:: tbot.named_testcase

Default Machine Access
----------------------
There are a few machines which can be configured in the *Configuration* and then accessed through the following functions.  This allows you to write generic testcases, based on using one or more of them:

.. autofunction:: tbot.acquire_lab
.. autofunction:: tbot.acquire_local
.. autofunction:: tbot.acquire_board
.. autofunction:: tbot.acquire_uboot
.. autofunction:: tbot.acquire_linux
