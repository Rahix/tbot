"""
Exports for git testcases
-------------------------
"""
import pathlib

EXPORT = ["GitRepository"]

class GitRepository(pathlib.PurePosixPath):
    """
    A meta object representing a git repository.
    Can be created with :func:`git_clean_checkout` or :func:`git_dirty_checkout`
    """
    pass
