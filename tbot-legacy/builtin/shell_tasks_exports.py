"""
Exports for shell operations
----------------------------
"""
import pathlib

EXPORT = ["TftpDirectory"]


class TftpDirectory:
    """
    A meta object to represent the tftp directory.
    Can be created with :func:`~tbot.builtin.shell_tasks.setup_tftpdir`

    :param pathlib.PurePosixPath root: TFTP root directory
    :param pathlib.PurePosixPath subdir: TFTP sub-directory

    :ivar root: TFTP root directory
    :ivar subdir: TFTP sub-directory, this is what you should use on the board
    :ivar path: Full TFTP path, this is what you should use on the Labhost
    """

    def __init__(
        self, root: pathlib.PurePosixPath, subdir: pathlib.PurePosixPath
    ) -> None:
        self.root = root
        self.subdir = subdir
        self.path = root / subdir
