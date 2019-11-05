from .. import linux


class Lab(linux.LinuxShell):
    """
    Mixin for marking a machine as a lab-host.
    """

    def build(self) -> linux.Builder:
        """
        Return the default build-host for this lab.

        If your lab does not contain a build-capable machine, just leave this
        method as is.  tbot will raise an exception if a testcase attempts
        accessing the build-host anyway.
        """
        raise KeyError("No build machine available!")
