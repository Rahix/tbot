.. py:module:: tbot.role

``tbot.role``
=============
Machine-roles as introduced in :ref:`tbot_role`.  You can also read more about
this in :ref:`configuration`.

.. autoclass:: tbot.role.Role

Predefined Roles
----------------
Here's a diagram with a rough outline of what each role is for.  Note that this
is entirely flexible though: E.g. you can use your localhost (= tbot-host) as
lab-host or have build-host and lab-host be the same machine just as well!

.. only:: html

   .. image:: ../static/tbot.svg

.. only:: latex

   .. image:: ../static/tbot.png

.. autoclass:: tbot.role.LabHost
.. autoclass:: tbot.role.BuildHost
.. autoclass:: tbot.role.LocalHost
.. autoclass:: tbot.role.Board
.. autoclass:: tbot.role.BoardUBoot
.. autoclass:: tbot.role.BoardLinux
