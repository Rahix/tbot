import time
import contextlib
from typing import Iterator, Union

import pytest

import tbot
from tbot import machine
from tbot.machine import board, channel, connector, linux
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


class LocalhostSlowBash(LocalhostBash, tbot.role.Role):
    name = "local-slow-bash"

    @property
    def workdir(self) -> linux.Path:
        return linux.Workdir.xdg_runtime(self, "selftest-data-bash-slow")

    def connect(self, mach: linux.LinuxShell) -> channel.Channel:
        ch = super().connect(mach)
        # Make the channel read one byte at a time, simulating a slow connection
        ch.READ_CHUNK_SIZE = 1
        return ch


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
            args = ("bash", "--posix", "--norc", "--noprofile", "--noediting")

        with super().subshell(*args):
            yield self

    def connect(self, mach: linux.LinuxShell) -> channel.Channel:
        # Make sure the terminal is wide enough to not cause breaks.
        mach.exec0("stty", "cols", "1024")
        return mach.open_channel(
            "bash", "--posix", "--norc", "--noprofile", "--noediting"
        )


# Different distros like to store this binary in different locations.  Thus we
# need to adapt to the system where tests are running to find the correct
# one...
SFTP_LOCATIONS = [
    "/usr/lib/ssh/sftp-server",
    "/usr/lib/openssh/sftp-server",
    "/usr/libexec/openssh/sftp-server",
]


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

        def path_exists(loc: str) -> bool:
            return linux.Path(self, loc).exists()

        sftp_location = next(filter(path_exists, SFTP_LOCATIONS), None)
        if sftp_location is not None:
            self._has_sftp = True
            sftp_config = f"# Make scp work\nSubsystem sftp {sftp_location}"
        else:
            self._has_sftp = False
            sftp_config = "# No sftp/scp available on this host."

        sshd_config = self.workdir / "sshd_config"
        sshd_config.write_text(
            f"""\
# Host Key
HostKey {keyfile.at_host(self)}

# Local Serving
ListenAddress localhost:18222

# Access
AuthorizedKeysFile none
AuthorizedKeysCommand {cat_path} {userkeypub.at_host(self)}
AuthorizedKeysCommandUser {self.env("USER")}
ChallengeResponseAuthentication no
UsePAM yes
PasswordAuthentication no
MaxAuthTries 1024

# Environment
AcceptEnv=XDG_RUNTIME_DIR

{sftp_config}
"""
        )

        sshd_path = self.exec0("which", "sshd").strip()

        self.exec0(sshd_path, "-D", "-f", sshd_config, linux.Background)
        sshd_pid = self.env("!")

        # Give the SSH server some time to get ready.
        time.sleep(0.5)

        try:
            yield None
        finally:
            out = self.exec0("true")
            if sshd_path not in out:
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
    _srv: MocksshServer

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
                srv.userkey.at_host(srv)
            )

            # Instanciate self
            m = cx.enter_context(cls(lo))
            m._srv = srv
            yield m

    @property
    def workdir(self) -> linux.Path:
        return linux.Workdir.xdg_runtime(self, "selftest-data-ssh-client")

    @property
    def has_sftp(self) -> bool:
        return getattr(self._srv, "_has_sftp", False)

    def init(self) -> None:
        self.exec0("rm", "-rf", self.workdir)
        self.exec0("mkdir", self.workdir)


class MockhwBoard(
    connector.ConsoleConnector,
    machine.PreConnectInitializer,
    board.PowerControl,
    board.Board,
    tbot.role.Role,
):
    name = "mockhw-board"

    @contextlib.contextmanager
    def _init_pre_connect(self) -> Iterator:
        workdir = linux.Workdir.xdg_runtime(self.host, "selftest-data-mockhw")
        self.host.exec0("rm", "-rf", workdir)
        self.host.exec0("mkdir", workdir)
        self._mockhw_script = workdir / "mockhw-script.sh"
        self._mockhw_script.write_text(
            """\
# This script "simulates" a serial session with a board.

# Make sure nothing enters the history
unset HISTFILE

# Disable commandline editing
set +o emacs
set +o vi

# Disable secondary prompt
PS2=""

# Simulated autoboot prompt
read -p "Autoboot: 3"

# Make this shell look a lot like U-Boot
PROMPT_COMMAND=
PS1='=> '
function version() {
    echo "Mockhw U-Boot, running in the most fake environment you can imagine."
    echo ""
    uname -a
}
function printenv() {
    if [ $# = 0 ]; then
        set | grep -E '^U'
    else
        set | grep "$1" | sed "s/'//g"
    fi
}
function setenv() {
    local var="$1"
    shift
    eval "$var=\\"$*\\""
}
function crc32() {
    printf "crc32 for %s ... %s ==> " "$1" "$1"
    sleep 0.2
    echo "deadb33f"
}
function boot() {
    echo "Pretending to boot Linux..."
    echo ""
    echo "[0.0000] Welcome to the simulation."
    read -p "Please press Enter to activate this console. GARBLE GARBLE"
    read -p "login: "
    read -s -p "password: "
    echo ""

    # Now undo the U-Boot hacks and make this look like a Linux
    PS1="bash@target-linux$ "
    unset -f printenv
    unset -f setenv
    unset -f version
}"""
        )
        self.host.exec0("chmod", "+x", self._mockhw_script)
        yield None

    def poweron(self) -> None:
        (self.host.workdir / "mockhw-power-status").write_text("on")

    def poweroff(self) -> None:
        (self.host.workdir / "mockhw-power-status").unlink(missing_ok=True)

    def connect(self, mach: linux.LinuxShell) -> channel.Channel:
        ch = mach.open_channel("bash", "--norc", "--noprofile", "--noediting", "-i")
        tbot.machine.linux.util.wait_for_shell(ch)
        ch.sendline(mach.escape("source", self._mockhw_script))
        return ch


class MockhwBoardUBoot(
    board.Connector, board.UBootAutobootIntercept, board.UBootShell, tbot.role.Role
):
    name = "mockhw-uboot"
    autoboot_prompt = tbot.Re(r"Autoboot: \d{0,10}")
    prompt = "=> "


class MockhwBoardLinux(
    board.LinuxUbootConnector,
    board.AskfirstInitializer,
    board.LinuxBootLogin,
    linux.Bash,
    tbot.role.Role,
):
    name = "mockhw-linux"

    uboot = MockhwBoardUBoot

    username = "root"
    password = "hunter2"


def register_machines(ctx: tbot.Context) -> None:
    ctx.register(Localhost, [Localhost, tbot.role.LabHost, tbot.role.LocalHost])
    ctx.register(LocalhostBash, [LocalhostBash])
    ctx.register(LocalhostSlowBash, [LocalhostSlowBash])
    ctx.register(LocalhostAsh, [LocalhostAsh])
    ctx.register(MocksshServer, [MocksshServer])
    ctx.register(MocksshClient, [MocksshClient])
    ctx.register(MockhwBoard, [MockhwBoard, tbot.role.Board])
    ctx.register(MockhwBoardUBoot, [MockhwBoardUBoot, tbot.role.BoardUBoot])
    ctx.register(MockhwBoardLinux, [MockhwBoardLinux, tbot.role.BoardLinux])
