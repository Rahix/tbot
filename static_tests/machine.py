from tbot.machine import connector, linux, shell


class DummyMach(connector.SubprocessConnector, shell.RawShell):
    name = "dummy"


class DummyLinuxMach(connector.SubprocessConnector, linux.Bash):
    name = "dummy-linux"
    username = "root"

    @property
    def workdir(self) -> "linux.Path[DummyLinuxMach]":
        return linux.Path(self, "/tmp/foo")


class DummyLinuxMach2(connector.SubprocessConnector, linux.Bash):
    name = "dummy-linux"
    username = "root"

    @property
    def workdir(self) -> "linux.Path[DummyLinuxMach2]":
        return linux.Path(self, "/tmp/foo")


def test_dummy() -> None:
    DummyMach()
