import typing
from tbot import machine
from tbot.machine import linux


class DummyMach(machine.Machine):
    name = "dummy"

    def destroy(self) -> None:
        pass


class DummyLinuxMach(linux.LinuxMachine):
    name = "dummy-linux"
    username = "root"

    @property
    def workdir(self) -> "linux.Path[DummyLinuxMach]":
        return linux.Path(self, "/tmp/foo")

    def destroy(self) -> None:
        pass

    def _obtain_channel(self) -> linux.paramiko.Channel:
        raise NotImplementedError()


class DummyLinuxMach2(linux.LinuxMachine):
    name = "dummy-linux"
    username = "root"

    @property
    def workdir(self) -> "linux.Path[DummyLinuxMach2]":
        return linux.Path(self, "/tmp/foo")

    def destroy(self) -> None:
        pass

    def _obtain_channel(self) -> linux.paramiko.Channel:
        raise NotImplementedError()

    def exec0(self, *args: "typing.Optional[str, linux.Path[DummyLinuxMach2]]", stdout="linux.Path[DummyLinuxMach2]") -> str: ...
    def exec(self, *args: "typing.Optional[str, linux.Path[DummyLinuxMach2]]", stdout="linux.Path[DummyLinuxMach2]") -> typing.Tuple[int, str]: ...


def test_dummy() -> None:
    mach = DummyMach()
