.. py:module:: tbot.tc

``tbot.tc`` - Builtin Testcases
===============================
tbot come bundled with a few builtin testcases.  Here is an overview:

Common
------
.. autofunction:: tbot.tc.testsuite


.. py:module:: tbot.tc.shell

Shell
-----
.. autofunction:: tbot.tc.shell.copy


.. py:module:: tbot.tc.git

Git
---
.. autoclass:: tbot.tc.git.GitRepository
   :members:


.. py:module:: tbot.tc.kconfig

Kconfig
-------
tbot has a few testcases to manipulate a kconfig-file, as used in Linux or U-Boot.  These are:

.. autofunction:: tbot.tc.kconfig.enable
.. autofunction:: tbot.tc.kconfig.module
.. autofunction:: tbot.tc.kconfig.disable
.. autofunction:: tbot.tc.kconfig.set_string_value
.. autofunction:: tbot.tc.kconfig.set_hex_value


.. py:module:: tbot.tc.uboot

U-Boot
------
tbot has testcases to automatically build U-Boot for your board.  These integrate nicely with the
:ref:`config-board`.

.. autofunction:: tbot.tc.uboot.build
.. autofunction:: tbot.tc.uboot.checkout
.. autoclass:: tbot.tc.uboot.UBootBuilder
    :members:
