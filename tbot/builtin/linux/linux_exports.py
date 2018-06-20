"""
Exports for Linux
-----------------
"""
from tbot import tc

EXPORT = ["LinuxRepository"]


class LinuxRepository(tc.GitRepository):
    """
    A meta object to represent a checked out version of Linux.
    Can be created with :func:`~tbot.builtin.linux.linux_tasks.linux_checkout`
    """
    pass
