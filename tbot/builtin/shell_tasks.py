"""
Common shell operations
-----------------------
"""
import pathlib
import typing
import tbot

@tbot.testcase
def setup_tftpdir(tb: tbot.TBot, *,
                  tftpdir: typing.Optional[pathlib.PurePosixPath] = None,
                 ) -> pathlib.PurePosixPath:
    """
    Setup the tftp directory

    :param tftpdir: Optional path to the tftpdir, defaults to
                    ``tb.config["tftp.directory"]`` (which has a default value
                    in ``config/tbot.py``
    :returns: The tftpdir
    """
    tftpdir = tftpdir or tb.config["tftp.directory"]

    if not isinstance(tftpdir, pathlib.PurePosixPath):
        raise Exception("Configuation error: 'tftp.directory' must be a PurePosixPath!")

    tb.shell.exec0(f"mkdir -p {tftpdir}", log_show=False)

    tb.log.log_debug(f"tftpdir is '{tftpdir}'")

    return tftpdir

@tbot.testcase
def cp_to_tftpdir(tb: tbot.TBot, *,
                  name: typing.Union[str, pathlib.PurePosixPath],
                  dest_name: typing.Optional[str] = None,
                  builddir: typing.Optional[pathlib.PurePosixPath] = None,
                  tftpdir: typing.Optional[pathlib.PurePosixPath] = None,
                 ) -> None:
    """
    Copy a file into the tftp folder

    :param name: Name of the file or path to the file
    :param dest_name: Name of the file inside the tftp folder, defaults to
                      the filename of ``name``
    :param builddir: Where to find files if no full path is supplied, defaults to
                     ``tb.config["uboot.builddir"]``
    :param tftpdir: Where to put files, defaults to ``tb.config["tftp.directory"]``
    """
    builddir = builddir or tb.config["uboot.builddir"]
    tftpdir = tftpdir or tb.config["tftp.directory"]

    source_path = builddir / name if isinstance(name, str) else name
    dest_path = tftpdir / (name if dest_name is None else dest_name)

    tb.log.log_debug(f"Copying '{source_path}' to '{dest_path}'")

    tb.shell.exec0(f"cp {source_path} {dest_path}")
