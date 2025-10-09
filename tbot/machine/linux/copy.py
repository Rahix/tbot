import typing

from tbot.machine import connector, linux
from tbot.machine.linux import auth

H1 = typing.TypeVar("H1", bound=linux.LinuxShell)
H2 = typing.TypeVar("H2", bound=linux.LinuxShell)


def _scp_copy(
    *,
    local_path: linux.Path[H1],
    remote_path: linux.Path[H2],
    copy_to_remote: bool,
    username: str,
    hostname: str,
    ignore_hostkey: bool,
    port: int,
    ssh_config: typing.List[str],
    authenticator: auth.Authenticator,
    use_multiplexing: bool,
    use_legacy_protocol: bool
) -> None:
    local_host = local_path.host

    hk_disable = ["-o", "StrictHostKeyChecking=no"] if ignore_hostkey else []

    scp_command = [
        "scp",
        *["-P", str(port)],
        *hk_disable,
        *[arg for opt in ssh_config for arg in ["-o", opt]],
    ]

    if use_multiplexing:
        multiplexing_dir = local_host.workdir / ".ssh-multi"
        scp_command += ["-o", "ControlMaster=auto"]
        scp_command += ["-o", "ControlPersist=10m"]
        scp_command += [
            "-o",
            f"ControlPath={multiplexing_dir.at_host(local_host)}/%C",
        ]
    
    if use_legacy_protocol:
        scp_command += ["-O"]

    if isinstance(authenticator, auth.NoneAuthenticator):
        scp_command += ["-o", "BatchMode=yes"]
    elif isinstance(authenticator, auth.PrivateKeyAuthenticator):
        scp_command += [
            "-o",
            "BatchMode=yes",
            "-i",
            authenticator.get_key_for_host(local_host),
        ]
    elif isinstance(authenticator, auth.PasswordAuthenticator):
        scp_command = ["sshpass", "-p", authenticator.password] + scp_command
    else:
        if typing.TYPE_CHECKING:
            authenticator._undefined_marker
        raise ValueError("Unknown authenticator {authenticator!r}")

    if copy_to_remote:
        local_host.exec0(
            *scp_command,
            local_path,
            f"{username}@{hostname}:{remote_path.at_host(remote_path.host)}",
        )
    else:
        local_host.exec0(
            *scp_command,
            f"{username}@{hostname}:{remote_path.at_host(remote_path.host)}",
            local_path,
        )


def copy(p1: linux.Path[H1], p2: linux.Path[H2], use_legacy_protocol: bool=False) -> None:
    """
    Copy a file, possibly from one host to another.

    The following transfers are currently supported:

    * ``H`` 🢥 ``H`` (transfer without changing host)
    * **lab-host** 🢥 **ssh-machine** (:py:class:`~tbot.machine.connector.SSHConnector`, using ``scp``)
    * **ssh-machine** 🢥 **lab-host** (Using ``scp``)
    * **local-host** 🢥 **paramiko-host** (:py:class:`~tbot.machine.connector.ParamikoConnector`, using ``scp``)
    * **local-host** 🢥 **ssh-machine** (:py:class:`~tbot.machine.connector.SSHConnector`, using ``scp``)
    * **paramiko-host**/**ssh-machine** 🢥 **local-host** (Using ``scp``)

    The following transfers are **not** supported:

    * **ssh-machine** 🢥 **ssh-machine** (There is no guarantee that two remote hosts can
      connect to each other.  If you need this, transfer to the lab-host first
      and then to the other remote)
    * **lab-host** 🢥 **board-machine** (Transfers over serial are not (yet) implemented.
      To 'upload' files, connect to your target via ssh or use a tftp download)

    :param linux.Path p1: Exisiting path to be copied
    :param linux.Path p2: Target where ``p1`` should be copied
    :param bool use_legacy_protocol: Use the legacy SCP protocol for file transfers 
        instead of the  SFTP  protocol (use -O option)

    .. note::

        You can combine this function with :py:func:`tbot_contrib.utils.hashcmp`
        to only copy a file when the hashsums of source and destination
        mismatch:

        .. code-block:: python

            from tbot_contrib import utils
            from tbot.tc import shell

            ...
            if not utils.hashcmp(path_a, path_b)
                shell.copy(path_a, path_b)

    .. versionadded:: 0.10.2
    """
    if isinstance(p1.host, p2.host.__class__) or isinstance(p2.host, p1.host.__class__):
        # Both paths are on the same host
        p2_w1 = linux.Path(p1.host, p2)
        p1.host.exec0("cp", p1, p2_w1)
        return
    elif isinstance(p1.host, connector.SSHConnector) and p1.host.host is p2.host:
        # Copy from an SSH machine
        _scp_copy(
            local_path=p2,
            remote_path=p1,
            copy_to_remote=False,
            username=p1.host.username,
            hostname=p1.host.hostname,
            ignore_hostkey=p1.host.ignore_hostkey,
            port=p1.host.port,
            ssh_config=p1.host.ssh_config,
            authenticator=p1.host.authenticator,
            use_multiplexing=p1.host.use_multiplexing,
            use_legacy_protocol=use_legacy_protocol,
        )
    elif isinstance(p2.host, connector.SSHConnector) and p2.host.host is p1.host:
        # Copy to an SSH machine
        _scp_copy(
            local_path=p1,
            remote_path=p2,
            copy_to_remote=True,
            username=p2.host.username,
            hostname=p2.host.hostname,
            ignore_hostkey=p2.host.ignore_hostkey,
            port=p2.host.port,
            ssh_config=p2.host.ssh_config,
            authenticator=p2.host.authenticator,
            use_multiplexing=p2.host.use_multiplexing,
            use_legacy_protocol=use_legacy_protocol,
        )
    elif isinstance(p1.host, connector.SubprocessConnector) and (
        isinstance(p2.host, connector.ParamikoConnector)
        or isinstance(p2.host, connector.SSHConnector)
    ):
        # Copy from local to ssh labhost
        _scp_copy(
            local_path=p1,
            remote_path=p2,
            copy_to_remote=True,
            username=p2.host.username,
            hostname=p2.host.hostname,
            ignore_hostkey=p2.host.ignore_hostkey,
            port=p2.host.port,
            ssh_config=getattr(p2.host, "ssh_config", []),
            authenticator=p2.host.authenticator,
            use_multiplexing=p2.host.use_multiplexing,
            use_legacy_protocol=use_legacy_protocol,
        )
    elif isinstance(p2.host, connector.SubprocessConnector) and (
        isinstance(p1.host, connector.ParamikoConnector)
        or isinstance(p1.host, connector.SSHConnector)
    ):
        # Copy to local from ssh labhost
        _scp_copy(
            local_path=p2,
            remote_path=p1,
            copy_to_remote=False,
            username=p1.host.username,
            hostname=p1.host.hostname,
            ignore_hostkey=p1.host.ignore_hostkey,
            port=p1.host.port,
            ssh_config=getattr(p2.host, "ssh_config", []),
            authenticator=p1.host.authenticator,
            use_multiplexing=p1.host.use_multiplexing,
            use_legacy_protocol=use_legacy_protocol,
        )
    else:
        raise NotImplementedError(f"Can't copy from {p1.host} to {p2.host}!")
