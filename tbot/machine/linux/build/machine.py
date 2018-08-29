import abc
import typing
from tbot.machine import linux
from . import toolchain


class BuildMachine(linux.LinuxMachine):
    """Generic buildhost machine."""

    @property
    @abc.abstractmethod
    def toolchains(self) -> typing.Dict[str, toolchain.Toolchain]:
        """
        Return a dictionary of all toolchains that exist on this buildhost.

        **Example**::

            @property
            def toolchains(self) -> typing.Dict[str, linux.build.Toolchain]:
                return {
                    "generic-armv7a": linux.build.EnvScriptToolchain(
                        linux.Path(
                            self,
                            "/path/to/environment-setup-armv7a-neon-poky-linux-gnueabi",
                        )
                    ),
                    "generic-armv7a-hf": linux.build.EnvScriptToolchain(
                        linux.Path(
                            self,
                            "/path/to/environment-setup-armv7ahf-neon-poky-linux-gnueabi",
                        )
                    ),
                }
        """
        pass

    def enable(self, arch: str) -> None:
        """
        Enable the toolchain for ``arch`` on this BuildHost instance.

        **Example**::

            with lh.default_build() as bh:
                bh.enable("generic-armv7a")

                bh.exec0(linux.Env("CC"), "--version")
        """
        tc = self.toolchains[arch]

        tc.enable(self)

    def __init__(
        self, arch: typing.Optional[str] = None, *args: typing.Any, **kwargs: typing.Any
    ) -> None:
        """
        Create a new BuildHost instance.

        :param str arch: Optionally enable the toolchain for ``arch``.
        :param args: Arguments for initializing the underlying linux machine.
        """
        super().__init__(*args, **kwargs)  # type: ignore

        if arch is not None:
            self.enable(arch)
