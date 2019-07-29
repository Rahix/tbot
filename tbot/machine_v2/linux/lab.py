from .. import linux


class Lab(linux.LinuxShell):
    def build(self) -> None:
        """Return the default build-host for this lab."""
        raise KeyError("No build machine available!")