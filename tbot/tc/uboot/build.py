# tbot, Embedded Automation Tool
# Copyright (C) 2019  Harald Seiler
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
import abc
import contextlib
import typing
import tbot
from tbot.machine import board, linux
from tbot.tc import git

H = typing.TypeVar("H", bound=linux.LinuxShell)
BH = typing.TypeVar("BH", bound=linux.Builder)


class UBootBuilder(abc.ABC):
    """
    U-Boot build process description.

    You will usually define it in your board config like this::

        class MyUBootBuilder(tbot.tc.uboot.UBootBuilder):
            name = "my-board"
            defconfig = "myboard_defconfig"
            toolchain = "generic-armv7a-hf"

    To make tbot aware of this config, you need to tell it in your
    U-Boot config::

        class MyUBootMachine(
            board.Connector,
            board.UBootShell,
        ):
            # Create a builder instance
            build = MyUBootBuilder()

    If you've done everything correctly, calling the ``uboot_checkout``
    or ``uboot_build`` testcases should then checkout and build U-Boot
    for your board!

    You can also manually trigger the checkout/build of a certain
    builder using the :meth:`~tbot.tc.uboot.UBootBuilder.checkout`
    and :meth:`~tbot.tc.uboot.UBootBuilder.build` methods.
    """

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Name of this builder."""
        pass

    remote = "https://git.denx.de/u-boot.git"
    """
    Where to fetch U-Boot from.
    """

    defconfig: typing.Optional[str] = None
    """
    Defconfig for this board.
    """

    toolchain: typing.Optional[str] = None
    """
    Name of the toolchain to be used.

    Must exist on the selected build-host.
    """

    def do_repo_path(self, bh: H) -> linux.Path[H]:
        """
        Build-Step that defines where the U-Boot build-directory is.

        The default path is ``$workdir/uboot-$name``.  Overwrite this
        step to set a custom path::

            def do_repo_path(self, bh: linux.Builder) -> linux.Path:
                return bh.workdir / "projects" / "foo" / "uboot"

        :param linux.Builder bh: Selected build-host.  The returned
            path **must** be associated with this machine.
        :rtype: linux.Path
        :returns: Path to the U-Boot build directory
        """
        return bh.workdir / f"uboot-{self.name}"

    def do_checkout(self, target: linux.Path[H], clean: bool) -> git.GitRepository[H]:
        """
        Build-Step that defines how to checkout U-Boot.

        Overwrite this step if you have a custom checkout procedure::

            def do_checkout(self, target: linux.Path, clean: bool) -> git.GitRepository:
                return git.GitRepository(
                    target=target,
                    url=self.remote,
                    clean=clean,
                    rev="v2018.09",
                )

        :param linux.Path target:  Where to checkout U-Boot to.  This build-step
            must be able to deal with an already checked out U-Boot source.
        :param bool clean: Whether this build-step should clean the source-dir
            (like ``git clean -fdx``).
        :rtype: tbot.tc.git.GitRepository
        :returns: A git repo of the checked out U-Boot sources
        """
        return git.GitRepository(target=target, url=self.remote, clean=clean)

    def do_patch(self, repo: git.GitRepository[H]) -> None:
        """
        Build-Step to patch the checked out U-Boot tree.

        If you need to apply patches ontop of upstream U-Boot, you should do
        so in this step::

            def do_patch(self, repo: git.GitRepository) -> None:
                repo.am(linux.Path(repo.host, "/path/to/patches"))
        """
        pass

    def do_toolchain(self, bh: BH) -> typing.ContextManager:
        """
        Build-Step to enable the toolchain.

        This step should return a context-manager for a sub-shell which has
        the toolchain enabled.  By default this step returns
        ``bh.enable(self.toolchain)``.
        """
        if self.toolchain is None:
            tbot.log.warning("No toolchain set, building native ...")
            return bh.subshell()
        else:
            return bh.enable(self.toolchain)

    def do_configure(self, bh: BH, repo: git.GitRepository[BH]) -> None:
        """
        Build-Step to generate the build configuration.

        By default, this steps runs ``make ${self.defconfig}``.
        """
        if self.defconfig is None:
            raise NotImplementedError("Can't build U-Boot without a defconfig")

        bh.exec0("make", self.defconfig)

    def do_build(self, bh: BH, repo: git.GitRepository[BH]) -> None:
        """
        Build-Step to actually build U-Boot.

        By default, this steps runs ``make -j $(nproc)``.
        """
        nproc = int(bh.exec0("nproc", "--all"))
        bh.exec0("make", "-j", str(nproc), "all")

    # --------------------------------------------------------------------------- #
    @staticmethod
    def _get_selected_builder() -> "UBootBuilder":
        builder = getattr(tbot.selectable.UBootMachine, "build")

        # This error message should make migration easier
        if isinstance(builder, type):
            raise AssertionError(
                f"""Builder must be an instance, not a type!
    You probably forgot to add `()` ...
    Got: {builder!r}"""
            )

        # Ensure type is correct
        assert isinstance(builder, UBootBuilder), f"{builder!r} is not a U-Boot Builder"

        return builder

    @tbot.named_testcase("uboot_checkout")
    def _checkout(
        builder: "typing.Optional[UBootBuilder]" = None,
        *,
        clean: bool = True,
        path: typing.Optional[linux.Path[H]] = None,
        host: typing.Optional[H] = None,
    ) -> git.GitRepository[H]:
        """
        Just checkout and patch a version of U-Boot without attempting to build it.

        This function can either be called with ``path`` which will make it checkout
        U-Boot to ``path`` or with ``host``, which will checkout U-Boot to the path
        defined in :meth:`~tbot.tc.uboot.UBootBuilder.do_repo_path`.

        Only on of ``path`` or ``host`` is allowed!
        """
        # If we don't have a builder, take the one for the selected board
        if builder is None:
            builder = UBootBuilder._get_selected_builder()

        # Assert this testcase is called correctly
        argslist = (path, host)
        assert (
            argslist.count(None) >= len(argslist) - 1
        ), "At most one of path or host can be specified!"

        tbot.log.message(f"Builder: {builder.name}")

        with contextlib.ExitStack() as cx:
            if path is not None:
                host = path.host
            else:
                if host is None:
                    lh = cx.enter_context(tbot.acquire_lab())
                    host = cx.enter_context(lh.build())

                path = builder.do_repo_path(host)

            repo = builder.do_checkout(path, clean)
            builder.do_patch(repo)

        return repo

    @tbot.named_testcase("uboot_build")
    def _build(
        builder: "typing.Optional[UBootBuilder]" = None,
        *,
        board: board.Board,
        clean: bool = True,
        repo: typing.Optional[git.GitRepository[BH]] = None,
        unpatched_repo: typing.Optional[git.GitRepository[BH]] = None,
        path: typing.Optional[linux.Path[BH]] = None,
        host: typing.Optional[BH] = None,
        lab: typing.Optional[linux.Lab] = None,
    ) -> git.GitRepository[BH]:
        """
        Build U-Boot.

        There are a few ways this testcase can be called:

        * From the commandline as ``uboot_build`` or in a testcase without
          any arguments:  tbot will use the configured build-host and builder
          config (see :class:`~tbot.tc.uboot.UBootBuilder`) to attempt building
          U-Boot.  You can use the ``clean`` parameter to specify whether the
          build should reuse existing artifacts or start from scratch.
        * Specifying just the ``lab`` parameter:  Use ``lab`` as the lab-host
          from where tbot should connect to its default build-host.
        * Specifying just the ``host`` parameter:  Build U-Boot on ``host``.
        * Just the ``path`` parameter:  Checkout U-Boot to ``path`` on ``path``'s
          associated host (which must be a build-host).
        * Only the ``unpatched_repo``:  Apply the patch step onto an already
          checked out revision before attempting the build.
        * Just the ``repo`` parameter:  Use the already checked-out revision
          that is assumed to already have necessary patches applied.

        In any case, tbot will attempt building U-Boot and if it succeeded,
        the testcase will return the git repo.  Depending on the way it was called,
        it will skip certain steps (See list above).  This can be used to build
        eg. with a pre-configured checkout or build in a bisect-run.

        You can only specify one of ``repo``, ``unpatched_repo``, ``path``, ``host``
        or ``lab``!

        If your build needs binary blobs to work you can define the
        ``add_blobs`` method in your board to handle this. It is passed the
        path to the build directory (which is also the repo directory). It can
        use shell.copy() to copy the files. Use path._local_str() to obtain the
        raw pathname to use if needed.

        :param bool clean:  Whether the U-Boot tree should be cleand of all leftovers
            from previous builds.
        :param git.GitRepository repo:  Build from existing, checkout-out revision.
        :param git.GitRepository unpatched_repo:  Build from existing, checkout-out revision,
            but also apply patches.
        :param linux.Path path:  Checkout U-Boot to ``path``.
        :param linux.BuildMachine host:  Build U-Boot on this host.
        :param linux.Lab lab:  Build U-Boot on the default build-host of this lab.
        :rtype: git.GitRepository
        :returns:  Location of the U-Boot tree containing build artifacts
        """
        # If we don't have a builder, take the one for the selected board
        if builder is None:
            builder = UBootBuilder._get_selected_builder()

        # Assert this testcase is called correctly
        argslist = (repo, unpatched_repo, path, host, lab)
        assert (
            argslist.count(None) >= len(argslist) - 1
        ), "At most one of repo, unpatched_repo, path, host, or lab can be specified!"

        with contextlib.ExitStack() as cx:
            if repo is not None:
                host = repo.host
            if unpatched_repo is not None:
                host = unpatched_repo.host
            elif path is not None:
                host = path.host
            elif host is None:
                if lab is None:
                    lab = cx.enter_context(tbot.acquire_lab())
                host = typing.cast(BH, cx.enter_context(lab.build()))

            if unpatched_repo is not None:
                repo = unpatched_repo
                builder.do_patch(repo)

            if repo is None:
                # Set host to none if we have a path
                checkout_host = host if path is None else None
                repo = checkout(builder, clean=clean, path=path, host=checkout_host)

            with builder.do_toolchain(host):
                host.exec0("cd", repo)

                if clean:
                    tbot.log.message("Cleaning previous build ...")
                    host.exec0("make", "mrproper")
                if not (repo / ".config").exists():
                    tbot.log.message("Configuring build ...")
                    builder.do_configure(host, repo)

                # Allow the board to copy in any required binary blobs
                board.add_blobs(repo)

                with tbot.testcase("uboot_make"):
                    builder.do_build(repo.host, repo)

        assert repo is not None
        return repo

    # We have to wrap the actual testcases so mypy does not complain
    # about invalid method signatures
    def checkout(
        self,
        *,
        clean: bool = True,
        path: typing.Optional[linux.Path[H]] = None,
        host: typing.Optional[H] = None,
    ) -> git.GitRepository[H]:
        """
        Just checkout and patch a version of U-Boot without attempting to build it.

        See :func:`tbot.tc.uboot.checkout`.
        """
        return UBootBuilder._checkout(self, clean=clean, path=path, host=host)

    def build(
        self,
        *,
        board: board.Board,
        clean: bool = True,
        repo: typing.Optional[git.GitRepository[BH]] = None,
        unpatched_repo: typing.Optional[git.GitRepository[BH]] = None,
        path: typing.Optional[linux.Path[BH]] = None,
        host: typing.Optional[BH] = None,
        lab: typing.Optional[linux.Lab] = None,
    ) -> git.GitRepository[BH]:
        """
        Build U-Boot.

        See :func:`tbot.tc.uboot.build`.
        """
        return UBootBuilder._build(
            self,
            board=board,
            clean=clean,
            repo=repo,
            unpatched_repo=unpatched_repo,
            path=path,
            host=host,
            lab=lab,
        )


# Export checkout and build as standalone functions
checkout = UBootBuilder._checkout
build = UBootBuilder._build
