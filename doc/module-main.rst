.. _mod:main:

``tbot`` Module
===============

.. autofunction:: tbot.testcase
.. autofunction:: tbot.named_testcase
.. autofunction:: tbot.acquire_lab
.. autofunction:: tbot.acquire_board
.. autofunction:: tbot.acquire_uboot
.. autofunction:: tbot.acquire_linux

.. py:data:: tbot.flags

    Flags that were set on the commandline using ``-f <flagname>``

    Check for a flag using::

        if "flagname" in tbot.flags:
            ...


``tbot.selectable``
-------------------
.. autoclass:: tbot.selectable.LabHost
.. autoclass:: tbot.selectable.Board
.. autoclass:: tbot.selectable.UBootMachine
.. autoclass:: tbot.selectable.LinuxMachine


``tbot.log``
------------
.. autoclass:: tbot.log.EventIO

Helpers
^^^^^^^
.. autoattribute:: tbot.log.IS_UNICODE

    Boolean that is set if stdout supports unicode.

    You should use :func:`tbot.log.u` instead of querying this flag.

.. autoattribute:: tbot.log.IS_COLOR

    Boolean that is set if tbot's output should be colored.

    You can use :class:`tbot.log.c` as an easy way to colorize your strings.

.. autofunction:: tbot.log.u

.. py:class:: tbot.log.c(s: str) -> tbot.log.c

    Color a string.  Reexport from :mod:`termcolor2`

    **Example**::

        tbot.log.message(tbot.log.c("Message").yellow.bold + ": Hello World!")

    :param str s: The string that should be colored

    .. py:attribute:: red

        Set the foreground-color to **red**

    .. py:attribute:: green

        Set the foreground-color to **green**

    .. py:attribute:: yellow

        Set the foreground-color to **yellow**

    .. py:attribute:: blue

        Set the foreground-color to **blue**

    .. py:attribute:: magenta

        Set the foreground-color to **magenta**

    .. py:attribute:: cyan

        Set the foreground-color to **cyan**

    .. py:attribute:: white

        Set the foreground-color to **white**


    .. py:attribute:: on_red

        Set the background-color to **red**

    .. py:attribute:: on_green

        Set the background-color to **green**

    .. py:attribute:: on_yellow

        Set the background-color to **yellow**

    .. py:attribute:: on_blue

        Set the background-color to **blue**

    .. py:attribute:: on_magenta

        Set the background-color to **magenta**

    .. py:attribute:: on_cyan

        Set the background-color to **cyan**

    .. py:attribute:: on_white

        Set the background-color to **white**


    .. py:attribute:: bold

        Enable the **bold** attribute

    .. py:attribute:: dark

        Enable the *dark* attribute

    .. py:attribute:: underline

        Enable the *underline* attribute

    .. py:attribute:: blink

        Enable the *blink* attribute

    .. py:attribute:: reverse

        Enable the *reverse* attribute

    .. py:attribute:: concealed

        Enable the *concealed* attribute


Log Events
^^^^^^^^^^
.. autofunction:: tbot.log.message
.. autofunction:: tbot.log_event.command
.. autofunction:: tbot.log_event.testcase_begin
.. autofunction:: tbot.log_event.testcase_end
