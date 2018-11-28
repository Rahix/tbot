.. highlight:: python
   :linenothreshold: 3

Building Projects
=================

tbot has a few facilities to ease building your projects.

Build-Host
----------
In tbot, your code is compiled on the so called build-host.  The build-host
should be defined in your lab-config and define the available toolchains.
To show how this works, I will make three examples:

Local Lab-Host as Build-Host
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
When using your localhost as the buildhost, you can no longer
omit the lab-config.  You have to define a very basic local lab,
which additionally also is a :class:`~tbot.machine.linux.BuildMachine`::

    from tbot.machine import linux

    class LocalLab(linux.lab.LocalLabHost, linux.BuildMachine):
        name = "local"

        @property
        def toolchains(self) -> typing.Dict[str, linux.build.Toolchain]:
            return {
                "generic-armv5te": linux.build.EnvScriptToolchain(
                    linux.Path(
                        self,
                        "/opt/yocto-2.4/generic-armv5te/environment-setup-armv5e-poky-linux-gnueabi",
                    )
                ),
                "generic-armv7a-hf": linux.build.EnvScriptToolchain(
                    linux.Path(
                        self,
                        "/opt/yocto-2.4/generic-armv7a-hf/environment-setup-armv7ahf-neon-poky-linux-gnueabi",
                    )
                ),
            }

        def build(self) -> "LocalLab":
            return self


    LAB = LocalLab

As you can see, this lab/build host defines two toolchains ``generic-armv5te`` and ``generic-armv7a-hf``.
You will see later how they can be used.

SSH Lab-Host as Build-Host
^^^^^^^^^^^^^^^^^^^^^^^^^^
Make you lab-host class inherit :class:`~tbot.machine.linux.BuildMachine` as shown in the example above
and define ``toolchains`` and ``build`` in a similar fashion.  There isn't much of a difference ...

Build-Host is another Machine
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
A lot of times, you have a separate server to build your projects.  tbot supports this as well.
The config will look like this::

    class BuildHostSSH(linux.SSHMachine, linux.BuildMachine):
        name = "my-buildhost"
        hostname = "build.localnet"

        @property
        def workdir(self) -> "linux.Path[BuildHostSSH]":
            return linux.Workdir.athome(self, "tbot-workdir")

        @property
        def toolchains(self) -> typing.Dict[str, linux.build.Toolchain]:
            return {
                "generic-armv5te": linux.build.EnvScriptToolchain(
                    linux.Path(
                        self,
                        "/opt/yocto-2.4/generic-armv5te/environment-setup-armv5e-poky-linux-gnueabi",
                    )
                ),
                "generic-armv6": linux.build.EnvScriptToolchain(
                    linux.Path(
                        self,
                        "/opt/yocto-2.4/generic-armv6/environment-setup-armv6-vfp-poky-linux-gnueabi",
                    )
                ),
                "generic-armv7a": linux.build.EnvScriptToolchain(
                    linux.Path(
                        self,
                        "/opt/yocto-2.4/generic-armv7a/environment-setup-armv7a-neon-poky-linux-gnueabi",
                    )
                ),
                "generic-armv7a-hf": linux.build.EnvScriptToolchain(
                    linux.Path(
                        self,
                        "/opt/yocto-2.4/generic-armv7a-hf/environment-setup-armv7ahf-neon-poky-linux-gnueabi",
                    )
                ),
                "generic-powerpc-e500v2": linux.build.EnvScriptToolchain(
                    linux.Path(
                        self,
                        "/opt/yocto-2.4/generic-powerpc-e500v2/environment-setup-ppce500v2-poky-linux-gnuspe",
                    )
                ),
            }


    class MyLab(lab.SSHLabHost):
        name = "my-lab"
        hostname = "lab.localnet"

        @property
        def workdir(self) -> "linux.path.Path[MyLab]":
            return linux.Workdir.athome(self, "tbot-workdir")

        def build(self) -> linux.BuildMachine:
            return BuildHostSSH(self)


    LAB = MyLab

For more info about configurable parameters, take a look at the :class:`~tbot.machine.linux.BuildMachine`
and :class:`~tbot.machine.linux.SSHMachine` classes.

Use Build-Host in Testcases
---------------------------
Using the build-host is pretty straight forward::

    with tbot.acquire_lab() as lh:
        with lh.build() as bh:
            # We now have a connection to the build-host
            bh.exec0("hostname")

            # Enable a specific toolchain for our project:
            with bh.enable("generic-armv7a-hf"):
                compiler = bh.env("CC")
                tbot.log.message(f"Compiler is {compiler!r}")

                # Commands to build your code
                bh.exec0("cd", bh.workdir / "my-project")
                bh.exec0("make")

:meth:`~tbot.machine.linux.BuildMachine.enable` is used to enable a toolchain.  The toolchain must be one that
is defined in your labconfig.

Building U-Boot
---------------
Because this is such a commonly needed program, tbot ships with a testcase to build U-Boot.  You can call
it from the commandline like this::

    tbot -l mylab.py -b boards/bbb.py uboot_build -vv


For this to work, your board-config has to specify some U-Boot build options::

    class BeagleBoneUBootBuild(denx.DenxUBootBuildInfo):
        name = "bbb"
        defconfig = "am335x_evm_defconfig"
        toolchain = "generic-armv7a-hf"

    class BeagleBoneUBoot(board.UBootMachine[BeagleBoneBlack]):
        prompt = "=> "
        build = BeagleBoneUBootBuild

    UBOOT = BeagleBoneUBoot

Take a look at :class:`~tbot.tc.uboot.BuildInfo` for available options.  And don't forget setting ``build``
in your ``UBootMachine``!
