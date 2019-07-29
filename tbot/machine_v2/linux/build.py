import abc
import contextlib
import typing

from . import linux_shell, path


class Toolchain(abc.ABC):
    """Generic toolchain type."""

    @abc.abstractmethod
    def enable(self, host: "Builder") -> None:
        """Enable this toolchain on the given ``host``."""
        pass


H = typing.TypeVar("H", bound="Builder")


class EnvScriptToolchain(Toolchain):
    """Toolchain that is initialized using an env script."""

    def enable(self, host: H) -> None:  # noqa: D102
        host.exec0("unset", "LD_LIBRARY_PATH")
        host.exec0("source", self.env_script)

    def __init__(self, path: path.Path[H]) -> None:
        """
        Create a new EnvScriptToolchain.

        :param linux.Path path: Path to the env script
        """
        self.env_script = path


class Builder(linux_shell.LinuxShell):
    @property
    @abc.abstractmethod
    def toolchains(self) -> typing.Dict[str, Toolchain]:
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

    @contextlib.contextmanager
    def enable(self, arch: str) -> typing.Iterator[None]:
        """
        Enable the toolchain for ``arch`` on this BuildHost instance.

        **Example**::

            with lh.build() as bh:
                # Now we are on the buildhost

                with bh.enable("generic-armv7a-hf"):
                    # Toolchain is enabled here
                    bh.exec0(linux.Env("CC"), "--version")
        """
        tc = self.toolchains[arch]

        with self.subshell():
            tc.enable(self)
            yield None
