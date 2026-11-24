.. py:module:: tbot.selectable

``tbot.selectable``
===================

.. warning::

   The :py:mod:`tbot.selectable` module is **deprecated** in favor of the new
   "tbot context" mechanism.  Please read the :ref:`context` guide for an
   introduction.

The :py:mod:`tbot.selectable` modules gets filled with the machines from
selected configuration at startup.  The following placeholders exist (which
will be replaced by proper machines):

.. autoclass:: tbot.selectable.LabHost
.. autoclass:: tbot.selectable.LocalLabHost
.. autoclass:: tbot.selectable.Board
.. autoclass:: tbot.selectable.UBootMachine
.. autoclass:: tbot.selectable.LinuxMachine
