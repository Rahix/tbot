"""
Common shell operations
-----------------------
"""
import pathlib
import typing
import tbot
from tbot import tc


@tbot.testcase
def setup_tftpdir(
    tb: tbot.TBot,
    *,
    root: typing.Optional[pathlib.PurePosixPath] = None,
    subdir: typing.Optional[pathlib.PurePosixPath] = None,
) -> tc.TftpDirectory:
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

    tftpdir = tc.TftpDirectory(root, subdir)

    tb.shell.exec0(f"mkdir -p {tftpdir.path}", log_show=False)

    tbot.log.debug(f"TFTP directory is '{tftpdir.path}'")

    return tftpdir


@tbot.testcase
def cp_to_tftpdir(
    tb: tbot.TBot,
    *,
    source: pathlib.PurePosixPath,
    dest_name: typing.Optional[str] = None,
    tftpdir: tc.TftpDirectory,
) -> None:
    dest_path = tftpdir.path / (source.name if dest_name is None else dest_name)

    tbot.log.debug(f"Copying '{source}' to '{dest_path}'")

    tb.shell.exec0(f"cp {source} {dest_path}")


@tbot.testcase
def retrieve_build_artifact(
    tb: tbot.TBot,
    *,
    buildfile: pathlib.PurePosixPath,
    buildhost: typing.Optional[str] = None,
    scp_command: typing.Optional[str] = None,
    scp_address: typing.Optional[str] = None,
) -> pathlib.PurePosixPath:
    """
    Copy artifacts from the buildhost to the labhost

    :param pathlib.PurePosixPath buildfile: File on the buildhost
    :param str buildhost: Name of the buildhost if you do not want to use
                          the default
    :param str scp_command: SCP command to use for copying (eg ``scp -i <..>``),
                            defaults to ``tb.config["build.<name>.scp_command"]``
    :param str scp_address: Address of the form ``<user>@<host>`` of the buildhost,
                            defaults to ``tb.config["build.<name>.scp_address"]``

                            .. todo:: Make use of ``username`` and ``hostname`` \
                                      parameters
    :returns: Path where the file has been copied
    :rtype: pathlib.PurePosixPath
    """
    buildhost = buildhost or tb.config["build.default", "<missing>"]
    bhcfg = f"build.{buildhost}."
    scp_command = scp_command or tb.config[bhcfg + "scp_command"]
    scp_address = scp_address or tb.config[bhcfg + "scp_address"]
    # TODO: Use <username> and <hostname> if address is not provided

    destination = tb.config["tbot.artifactsdir"] / buildfile.name
    if not isinstance(destination, pathlib.PurePosixPath):
        raise Exception("config error, tbot.artifactsdir must be a path")
    tbot.log.debug(f"cp {buildfile} (build) -> {destination} (lab)")

    tb.machines["labhost-noenv"].exec0(f"mkdir -p {destination.parent}", log_show=False)
    tb.machines["labhost-noenv"].exec0(
        f"{scp_command} {scp_address}:{buildfile} {destination}", log_show=False
    )

    return destination
