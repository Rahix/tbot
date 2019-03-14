.. _recipes:recipes:

Recipes
=======

Recipes are supposed to be code snippets that can be used in your testcases
to make development faster.

Testcase with Lab
-----------------
A testcase that interacts with the lab should be able to take the LabHost
as a parameter, so it won't open a parallel connection each time::

    import typing
    import tbot
    from tbot.machine import linux

    @tbot.testcase
    def my_testcase(
        lab: typing.Optional[linux.LabHost] = None,
    ) -> None:
        with lab or tbot.acquire_lab() as lh:
            lh.exec0("uname", "-a")

.. _recipes:testcase with u-boot:

Testcase with U-Boot
--------------------
A testcase that interacts with U-Boot should be able to take the U-Boot
machine as a paramter as long as it does not require the board to powercycle,
etc.

::

    import contextlib
    import typing
    import tbot
    from tbot.machine import board


    @tbot.testcase
    def my_testcase(
        lab: typing.Optional[tbot.selectable.LabHost] = None,
        uboot: typing.Optional[board.UBootMachine] = None,
    ) -> None:
        with contextlib.ExitStack() as cx:
            lh = cx.enter_context(lab or tbot.acquire_lab())
            if uboot is not None:
                ub = uboot
            else:
                b = cx.enter_context(tbot.acquire_board(lh))
                ub = cx.enter_context(tbot.acquire_uboot(b))

            ub.exec0("version")

Testcase with Board Linux
-------------------------
A testcase that is supposed to be run on the boards linux should be able
to take the BoardLinux machine as a paramter as long as it does not require
powercycling, etc.

::

    import contextlib
    import typing
    import tbot
    from tbot.machine import board


    @tbot.testcase
    def test_testcase(
        lab: typing.Optional[tbot.selectable.LabHost] = None,
        board_linux: typing.Optional[board.LinuxMachine] = None,
    ) -> None:
        with contextlib.ExitStack() as cx:
            lh = cx.enter_context(lab or tbot.acquire_lab())
            if board_linux is not None:
                lnx = board_linux
            else:
                b = cx.enter_context(tbot.acquire_board(lh))
                lnx = cx.enter_context(tbot.acquire_linux(b))

            lnx.exec0("uname", "-a")


Testcase that initializes Board
-------------------------------
If you just need to power on the board once, use the following snippet::

    import contextlib
    import typing
    import tbot
    from tbot.machine import board


    @tbot.testcase
    def test_testcase(
        lab: typing.Optional[tbot.selectable.LabHost] = None,
    ) -> None:
        with contextlib.ExitStack() as cx:
            lh = cx.enter_context(lab or tbot.acquire_lab())
            b = cx.enter_context(tbot.acquire_board(lh))
            lnx = cx.enter_context(tbot.acquire_linux(b))

            ...


Rebooting
^^^^^^^^^
If your testcase is one that is more complex and requires the board
to powercycle at some point, you could write a testcase like this::

    import contextlib
    import typing
    import tbot
    from tbot.machine import board


    @tbot.testcase
    def test_testcase(
        lab: typing.Optional[tbot.selectable.LabHost] = None,
    ) -> None:
        with lab or tbot.acquire_lab() as lh:
            with contextlib.ExitStack() as cx:
                b = cx.enter_context(tbot.acquire_board(lh))
                lnx = cx.enter_context(tbot.acquire_linux(b))

                ...

             # Board is off now, repeat the last context to turn it
             # on again:
            with contextlib.ExitStack() as cx:
                b = cx.enter_context(tbot.acquire_board(lh))
                lnx = cx.enter_context(tbot.acquire_linux(b))

                ...


Build on your Localhost regardless of selected LabHost
------------------------------------------------------
Sometimes you want to build something on your machine (tbot Host) and not in
the lab.  Eg. when you want to hack on the code and have tbot automate the build and deploy
process::

    import contextlib
    import typing
    import tbot
    from tbot.machine import linux
    from tbot.tc import shell


    @tbot.testcase
    def build_my_code() -> None:
        with tbot.acquire_local() as lo:
            lo.exec0("cd", lo.tbotdir)
            lo.exec0("sphinx-build", "-M", "html", "doc/", "doc/_build/")
            lo.exec0("cd", "doc/_build")
            lo.exec0("tar", "czvf", "documentation.tgz", "html")

    @tbot.testcase
    def upload_my_code(
        lab: typing.Optional[linux.LabHost] = None,
    ) -> None:
        with contextlib.ExitStack() as cx:
            lo = cx.enter_context(tbot.acquire_local())
            lh = cx.enter_context(lab or tbot.acquire_lab())
            shell.copy(
                linux.Path(lo, "/home/hws/Documents/Developing/tbot/doc/_build/documentation.tgz"),
                lh.workdir / "doc.tgz",
            )


Download artifacts to tbot Host
-------------------------------
Especially in a CI setting you might want to store build artifacts next to the log.  You can do so
using the ``copy`` testcase that is built into tbot.  Do note however, that you can't download
artifacts directly from e.g. the buildhost.  To do that, first copy them to the LabHost and download
them from there.  Here's example code::

    import contextlib
    import typing
    import tbot
    from tbot.machine import linux
    from tbot.tc import shell

    @tbot.testcase
    def test_download(
        lab: typing.Optional[linux.LabHost] = None,
    ) -> None:
        with contextlib.ExitStack() as cx:
            lo = cx.enter_context(tbot.acquire_local())
            lh = cx.enter_context(lab or tbot.acquire_lab())
            shell.copy(
                lh.workdir / "doc.tgz",
                linux.Path(lo, "/tmp/documentation.tgz"),
            )

.. _recipes:bisect:

Bisect a git repository
-----------------------
When a new version of your software has introduced a bug, *git-bisect* is
a very helpful tool for narrowing down the cause;  tbot can automate this with
just a little bit of code::

    import typing
    import tbot
    from tbot.machine import linux
    from tbot.tc import git


    @tbot.testcase
    def bisect_myrepo(
        lab: typing.Optional[linux.LinuxMachine] = None,
    ) -> None:
        with lab or tbot.acquire_lab() as lh:
            repo = git.GitRepository(
                linux.Path(lh, "/home/hws/foo/bar"),
                clean=False,
            )

            @tbot.testcase
            def check_revision(_: git.GitRepository) -> bool:
                # Ensure we have a pristine repository to
                # reduce side effects
                repo.clean(True, True, True)

                lh.exec0("cd", repo)
                lh.exec0("make")

                # Run your test that triggers the bug
                # if the commit is bad, return False
                # if the commit is good, return True
                return False

            bad = repo.bisect(
                good="known-good-revision",
                # tbot will test if this revision is actually good!
                # It will also test if the current revision is actuall bad,
                # so it is ensured that your test gives proper results before
                # bisecting
                test=check_revision,
            )

            tbot.log.message(f"First bad commit is {bad}!")
