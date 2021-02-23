import contextlib
from typing import Iterator, Union

import pytest
import tbot
from tbot import machine
from tbot.machine import channel, connector, linux
from tbot.tc import shell


class Localhost(connector.SubprocessConnector, linux.Bash, tbot.role.Role):
    name = "local"

    @property
    def workdir(self) -> linux.Path:
        return linux.Workdir.xdg_runtime(self, "selftest-data")

    def init(self) -> None:
        self.exec0("rm", "-rf", self.workdir)
        self.exec0("mkdir", self.workdir)


class LocalhostBash(connector.ConsoleConnector, linux.Bash, tbot.role.Role):
    name = "local-bash"

    @property
    def workdir(self) -> linux.Path:
        return linux.Workdir.xdg_runtime(self, "selftest-data-bash")

    def init(self) -> None:
        self.exec0("rm", "-rf", self.workdir)
        self.exec0("mkdir", self.workdir)

    def connect(self, mach: linux.LinuxShell) -> channel.Channel:
        return mach.open_channel("bash", "--norc", "--noprofile")


class LocalhostAsh(connector.ConsoleConnector, linux.Ash, tbot.role.Role):
    name = "local-ash"

    @property
    def workdir(self) -> linux.Path:
        return linux.Workdir.xdg_runtime(self, "selftest-data-ash")

    def init(self) -> None:
        self.exec0("rm", "-rf", self.workdir)
        self.exec0("mkdir", self.workdir)

    @contextlib.contextmanager
    def subshell(
        self, *args: Union[str, linux.special.Special, linux.Path]
    ) -> "Iterator[LocalhostAsh]":
        # Patch the shell invocation command if no args are given because we're
        # not using real `ash` here ...
        if len(args) == 0:
            args = ("bash", "--posix", "--norc", "--noprofile")

        with super().subshell(*args):
            yield self

    def connect(self, mach: linux.LinuxShell) -> channel.Channel:
        # Make sure the terminal is wide enough to not cause breaks.
        mach.exec0("stty", "cols", "1024")
        return mach.open_channel("bash", "--posix", "--norc", "--noprofile")


class MocksshServer(
    connector.SubprocessConnector,
    linux.Bash,
    machine.PostShellInitializer,
    tbot.role.Role,
):
    name = "mockssh-server"

    @property
    def workdir(self) -> linux.Path:
        return linux.Workdir.xdg_runtime(self, "selftest-data-ssh")

    @contextlib.contextmanager
    def _init_post_shell(self) -> Iterator[None]:
        # Make sure all requirements are available
        for tool in ["ssh", "ssh-keygen", "sshd"]:
            if not shell.check_for_tool(self, tool):
                pytest.skip(f"Skipping ssh tests because `{tool}` is missing.")

        self.exec0("mkdir", "-p", self.workdir)
        self.exec0("chmod", "0700", self.workdir)

        keyfile = self.workdir / "ssh_host_rsa_key"
        if not keyfile.exists():
            self.exec0("ssh-keygen", "-f", keyfile, "-N", "", "-t", "rsa")

        userkey = self.workdir / "id_rsa"
        userkeypub = self.workdir / "id_rsa.pub"
        if not userkey.exists():
            self.exec0("ssh-keygen", "-f", userkey, "-N", "", "-t", "rsa")
            self.exec0("chmod", "0600", userkeypub)

        self.userkey = userkey

        cat_path = self.exec0("which", "cat").strip()

        sshd_config = self.workdir / "sshd_config"
        sshd_config.write_text(
            f"""\
# Host Key
HostKeyAlgorithms ssh-rsa
HostKey {keyfile._local_str()}

# Local Serving
ListenAddress localhost:18222

# Access
AuthorizedKeysFile none
AuthorizedKeysCommand {cat_path} {userkeypub._local_str()}
AuthorizedKeysCommandUser {self.env("USER")}
ChallengeResponseAuthentication no
UsePAM yes
PasswordAuthentication no

# Environment
AcceptEnv=XDG_RUNTIME_DIR"""
        )

        sshd_path = self.exec0("which", "sshd").strip()

        self.exec0(sshd_path, "-D", "-f", sshd_config, linux.Background)
        sshd_pid = self.env("!")

        try:
            yield None
        finally:
            self.exec0("kill", sshd_pid, linux.Then, "wait", sshd_pid)


class MocksshClient(connector.SSHConnector, linux.Bash, tbot.role.Role):
    name = "mockssh-client"

    # SSH Settings
    hostname = "localhost"
    ignore_hostkey = True
    port = 18222
    ssh_config = ["UserKnownHostsFile=/dev/null", "SendEnv=XDG_RUNTIME_DIR"]
    # will be overridden later:
    authenticator = linux.auth.PrivateKeyAuthenticator("/dev/null")

    @classmethod
    @contextlib.contextmanager
    def from_context(cls, ctx: tbot.Context) -> Iterator:
        with contextlib.ExitStack() as cx:
            # Start the server
            srv = cx.enter_context(ctx.request(MocksshServer))
            # Get a localhost
            lo = cx.enter_context(ctx.request(tbot.role.LocalHost))

            # Set authenticator
            cls.authenticator = linux.auth.PrivateKeyAuthenticator(
                srv.userkey._local_str()
            )

            # Instanciate self
            m = cx.enter_context(cls(lo))
            yield m

    @property
    def workdir(self) -> linux.Path:
        return linux.Workdir.xdg_runtime(self, "selftest-data-ssh-client")

    def init(self) -> None:
        self.exec0("rm", "-rf", self.workdir)
        self.exec0("mkdir", self.workdir)


def register_machines(ctx: tbot.Context) -> None:
    ctx.register(Localhost, [Localhost, tbot.role.LabHost, tbot.role.LocalHost])
    ctx.register(LocalhostBash, [LocalhostBash])
    ctx.register(LocalhostAsh, [LocalhostAsh])
    ctx.register(MocksshServer, [MocksshServer])
    ctx.register(MocksshClient, [MocksshClient])
