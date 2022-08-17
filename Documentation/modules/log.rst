.. py:module:: tbot.log

``tbot.log``
============
tbot has its own logging mechanism to provide pretty output during a testcase
run and extensive information about it afterwards.  The :py:mod:`tbot.log`
module contains the relevant code.  Basically, everything centers about
:py:class:`~tbot.log.EventIO` objects, which represent single log-events.
These can either be created using one of the many existing log-event function,
or manually, if the existing ones are not covering your case.

Helpers
-------
.. autofunction:: tbot.log.with_verbosity

.. py:attribute:: IS_UNICODE

    Boolean that is set if stdout supports unicode.

    You should use :func:`tbot.log.u` instead of querying this flag.

.. py:attribute:: IS_COLOR

    Boolean that is set if tbot's output should be colored.

    You can use :class:`tbot.log.c() <tbot.log.c>` as an easy way to colorize your strings.

.. autofunction:: u

.. py:class:: c(s: str) -> tbot.log.c

    Color a string.  Reexport from |termcolor2|_

    .. |termcolor2| replace:: ``termcolor2``
    .. _termcolor2: https://pypi.org/project/termcolor2/

    **Example**::

        tbot.log.message(tbot.log.c("Message").yellow.bold + ": Hello World!")

    :param str s: The string that should be colored

    The following 'attributes' exist to restyle the text:

    ================ ================ ===============
    Foreground Color Background Color Style Attribute
    ================ ================ ===============
    **.red**         **.on_red**      **.bold**
    **.green**       **.on_green**    **.dark**
    **.yellow**      **.on_yellow**   **.underline**
    **.blue**        **.on_blue**     **.blink**
    **.magenta**     **.on_magenta**  **.reverse**
    **.cyan**        **.on_cyan**     **.concealed**
    **.white**       **.on_white**
    ================ ================ ===============

Log Events
----------
.. autofunction:: tbot.log.message
.. autofunction:: tbot.log.warning
.. autofunction:: tbot.log.skip
.. autofunction:: tbot.log_event.command
.. autofunction:: tbot.log_event.testcase_begin
.. autofunction:: tbot.log_event.testcase_end

``EventIO``
-----------
.. autoclass:: tbot.log.EventIO
