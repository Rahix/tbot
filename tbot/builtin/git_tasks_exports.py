"""
Exports for git testcases
-------------------------
"""
import pathlib

EXPORT = ["GitRepository"]

class GitRepository(pathlib.PurePosixPath):
    """
    A meta object representing a git repository.
    Can be created with :func:`~tbot.builtin.git_tasks.git_clean_checkout` or
    :func:`~tbot.builtin.git_tasks.git_dirty_checkout`
    """
    pass
