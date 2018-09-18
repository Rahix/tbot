import typing
import tbot
from tbot.machine import linux
from tbot.machine.linux import auth

H = typing.TypeVar("H", bound=linux.LinuxMachine)


@tbot.testcase
def copy(p1: linux.Path[H], p2: linux.Path[H]) -> None:
    """
    Copy a file, possibly from one host to another.

    If one of the paths is associated with an SSHMachine,
    ``scp`` will be used to do the transfer.

    :param linux.Path p1: Exisiting path to be copied
    :param linux.Path p2: Target where ``p1`` whould be copied
    """
    if p1.host is p2.host:
        # Both paths are on the same host
        p1.host.exec0("cp", p1, p2)
    elif isinstance(p1.host, linux.SSHMachine) and p1.host.labhost is p2.host:
        authenticator = p1.host.authenticator
        if not isinstance(authenticator, auth.PrivateKeyAuthenticator):
            raise RuntimeError("Only key authentication is supported")
        key = authenticator.key

        # Copy from an ssh host
        p2.host.exec0(
            "scp",
            "-P",
            str(p1.host.port),
            "-o",
            "BatchMode=yes",
            "-i",
            str(key),
            f"{p1.host.username}@{p1.host.hostname}:{p1._local_str()}",
            p2,
        )
    elif isinstance(p2.host, linux.SSHMachine) and p2.host.labhost is p1.host:
        authenticator = p2.host.authenticator
        if not isinstance(authenticator, auth.PrivateKeyAuthenticator):
            raise RuntimeError("Only key authentication is supported")
        key = authenticator.key

        # Copy to an ssh host
        p1.host.exec0(
            "scp",
            "-P",
            str(p2.host.port),
            "-o",
            "BatchMode=yes",
            "-i",
            str(key),
            p1,
            f"{p2.host.username}@{p2.host.hostname}:{p2._local_str()}",
        )
    else:
        raise NotImplementedError(f"Can't copy from {p1.host} to {p2.host}!")
