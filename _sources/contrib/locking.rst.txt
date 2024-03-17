.. py:module:: tbot_contrib.locking

``tbot_contrib.locking``
========================
This module provide utilities for managing "locks" on the lab-host.  This can be
used in setups where multiple users might try accessing the same host at the
same time.  Instead of cryptic errors due to busy devices or, even worse, bad
behavior because of two running tbot testcases interfering, only one can ever
access, for example, a board.

To facilitate this, two parts are needed:

1. The lab-host configuration must be augmented with the
   :py:class:`~tbot_contrib.locking.LockManager` mixin.  This provides a locking
   "implementation" which board machines can hook into.

2. To enable locking for a certain board, it should inherit the
   :py:class:`~tbot_contrib.locking.MachineLock` mixin.

.. autoclass:: tbot_contrib.locking.MachineLock
   :members:

.. autoclass:: tbot_contrib.locking.LockManager
   :members:
