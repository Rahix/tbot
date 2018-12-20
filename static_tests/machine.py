from tbot import machine
from tbot.machine import linux
from tbot.machine import channel


class DummyMach(machine.Machine):
    name = "dummy"

    @property
    def lh(self) -> linux.LabHost:
        raise NotImplementedError()

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

    @property
    def lh(self) -> linux.LabHost:
        raise NotImplementedError()

    def _obtain_channel(self) -> channel.Channel:
        raise NotImplementedError()


class DummyLinuxMach2(linux.LinuxMachine):
    name = "dummy-linux"
    username = "root"

    @property
    def workdir(self) -> "linux.Path[DummyLinuxMach2]":
        return linux.Path(self, "/tmp/foo")

    def destroy(self) -> None:
        pass

    @property
    def lh(self) -> linux.LabHost:
        raise NotImplementedError()

    def _obtain_channel(self) -> channel.Channel:
        raise NotImplementedError()


def test_dummy() -> None:
    mach = DummyMach()
