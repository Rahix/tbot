import typing
import tbot
from tbot.machine import linux
from tbot.machine.linux import auth

__all__ = ("copy",)

H1 = typing.TypeVar("H1", bound=linux.LinuxMachine)
H2 = typing.TypeVar("H2", bound=linux.LinuxMachine)


def _scp_copy(
    *,
    local_path: linux.Path[H1],
    remote_path: linux.Path[H2],
    copy_to_remote: bool,
    username: str,
    hostname: str,
    ignore_hostkey: bool,
    port: int,
    authenticator: auth.Authenticator,
) -> None:
    local_host = local_path.host

    hk_disable = ["-o", "StrictHostKeyChecking=no"] if ignore_hostkey else []

    scp_command = ["scp", "-P", str(port), *hk_disable]

    if isinstance(authenticator, auth.PrivateKeyAuthenticator):
        scp_command += ["-o", "BatchMode=yes", "-i", str(authenticator.key)]
    elif isinstance(authenticator, auth.PasswordAuthenticator):
        scp_command = ["sshpass", "-p", authenticator.password] + scp_command

    if copy_to_remote:
        local_host.exec0(
            *scp_command,
            local_path,
            f"{username}@{hostname}:{remote_path._local_str()}",
        )
    else:
        local_host.exec0(
            *scp_command,
            f"{username}@{hostname}:{remote_path._local_str()}",
            local_path,
        )


@tbot.testcase
def copy(p1: linux.Path[H1], p2: linux.Path[H2]) -> None:
    """
    Copy a file, possibly from one host to another.

    If one of the paths is associated with an SSHMachine,
    ``scp`` will be used to do the transfer.

    :param linux.Path p1: Exisiting path to be copied
    :param linux.Path p2: Target where ``p1`` should be copied
    """
    if isinstance(p1.host, p2.host.__class__) or isinstance(p2.host, p1.host.__class__):
        # Both paths are on the same host
        p2_w1 = linux.Path(p1.host, p2)
        p1.host.exec0("cp", p1, p2_w1)
        return
    elif isinstance(p1.host, linux.SSHMachine) and p1.host.labhost is p2.host:
        # Copy from an SSH machine
        _scp_copy(
            local_path=p2,
            remote_path=p1,
            copy_to_remote=False,
            username=p1.host.username,
            hostname=p1.host.hostname,
            ignore_hostkey=p1.host.ignore_hostkey,
            port=p1.host.port,
            authenticator=p1.host.authenticator,
        )
    elif isinstance(p2.host, linux.SSHMachine) and p2.host.labhost is p1.host:
        # Copy to an SSH machine
        _scp_copy(
            local_path=p1,
            remote_path=p2,
            copy_to_remote=True,
            username=p2.host.username,
            hostname=p2.host.hostname,
            ignore_hostkey=p2.host.ignore_hostkey,
            port=p2.host.port,
            authenticator=p2.host.authenticator,
        )
    elif isinstance(p1.host, linux.lab.LocalLabHost) and isinstance(
        p2.host, linux.lab.SSHLabHost
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
            authenticator=p2.host.authenticator,
        )
    elif isinstance(p2.host, linux.lab.LocalLabHost) and isinstance(
        p1.host, linux.lab.SSHLabHost
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
            authenticator=p1.host.authenticator,
        )
    else:
        raise NotImplementedError(f"Can't copy from {p1.host} to {p2.host}!")
