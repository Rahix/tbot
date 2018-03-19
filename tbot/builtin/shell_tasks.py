"""
Common shell operations
-----------------------
"""
import pathlib
import typing
import tbot

EXPORT = ["TftpDirectory"]

class TftpDirectory:
    """
    A meta object to represent the tftp directory.
    Can be created with :func:`setup_tftpdir`

    :param root: TFTP root directory
    :type root: pathlib.PurePosixPath
    :param subdir: TFTP sub-directory
    :type subdir: pathlib.PurePosixPath

    :ivar root: TFTP root directory
    :ivar subdir: TFTP sub-directory, this is what you should use on the board
    :ivar path: Full TFTP path, this is what you should use on the Labhost
    """

    def __init__(self,
                 root: pathlib.PurePosixPath,
                 subdir: pathlib.PurePosixPath) -> None:
        self.root = root
        self.subdir = subdir
        self.path = root / subdir

@tbot.testcase
def setup_tftpdir(tb: tbot.TBot, *,
                  root: typing.Optional[pathlib.PurePosixPath] = None,
                  subdir: typing.Optional[pathlib.PurePosixPath] = None,
                 ) -> TftpDirectory:
    """
    Setup the tftp directory

    :param root: Optional path to the TFTP root directory, defaults to
                    ``tb.config["tftp.root"]``
    :type root: pathlib.PurePosixPath
    :param subdir: Optional subdir path inside the TFTP directory (has a
                   default value in ``config/tbot.py``)
    :type subdir: pathlib.PurePosixPath
    :returns: The TFTP directory as a meta object
    :rtype: TftpDirectory
    """
    root = root or tb.config["tftp.root"]
    subdir = subdir or tb.config["tftp.directory"]

    if not isinstance(root, pathlib.PurePosixPath):
        raise Exception("Configuation error: 'tftp.root' must be a PurePosixPath!")
    if not isinstance(subdir, pathlib.PurePosixPath):
        raise Exception("Configuation error: 'tftp.directory' must be a PurePosixPath!")

    tftpdir = TftpDirectory(root, subdir)

    tb.shell.exec0(f"mkdir -p {tftpdir.path}", log_show=False)

    tb.log.log_debug(f"TFTP directory is '{tftpdir.path}'")

    return tftpdir

@tbot.testcase
def cp_to_tftpdir(tb: tbot.TBot, *,
                  name: typing.Union[str, pathlib.PurePosixPath],
                  dest_name: typing.Optional[str] = None,
                  builddir: typing.Optional[pathlib.PurePosixPath] = None,
                  tftpdir: TftpDirectory,
                 ) -> None:
    """
    Copy a file into the tftp folder

    :param name: Name of the file or path to the file
    :type name: str, pathlib.PurePosixPath
    :param dest_name: Name of the file inside the tftp folder, defaults to
                      the filename of ``name``
    :type dest_name: str
    :param builddir: Where to find files if no full path is supplied, defaults to
                     ``tb.config["uboot.builddir"]``
    :type builddir: pathlib.PurePosixPath
    :param tftpdir: Where to put the file
    :type tftpdir: TftpDirectory
    """
    builddir = builddir or tb.config["uboot.builddir"]

    source_path = builddir / name if isinstance(name, str) else name
    dest_path = tftpdir.path / (name if dest_name is None else dest_name)

    tb.log.log_debug(f"Copying '{source_path}' to '{dest_path}'")

    tb.shell.exec0(f"cp {source_path} {dest_path}")
