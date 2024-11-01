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

import typing
import tbot
import enum
from tbot.machine import linux

H = typing.TypeVar("H", bound=linux.LinuxShell)


class ResetMode(enum.Enum):
    """Mode for ``git --reset``."""

    SOFT = "--soft"
    MIXED = "--mixed"
    HARD = "--hard"
    MERGE = "--merge"
    KEEP = "--keep"


class GitRepository(linux.Path[H]):
    """Git repository."""

    def __init__(
        self,
        target: linux.Path[H],
        url: typing.Optional[str] = None,
        *,
        clean: bool = True,
        fetch: bool = True,
        rev: typing.Optional[str] = None,
    ) -> None:
        """
        Initialize a git repository from either a remote or an existing repo.

        There are two modes in which a repo can be initialized:

        1. Only supplying ``target``: tbot assumes, that a repo exists at ``target``
           already and will fail if this is not the case.
        2. Also supplying ``url``: If ``target`` is not already a git repo, one will
           be created by cloning ``url``.

        If ``clean`` is ``True``, the repo will be hard reset and all untracked
        files/ changes will be removed. If ``rev`` is also given, it will be
        checked out.

        If ``fetch`` is ``True`` and ``url`` is given, the latest upstream revision
        will be checked out.

        :param linux.Path target: Where the repository is supposed to be.
        :param str url: Optional remote url. Whether this is set specifies the
            mode the repo is initialized in.
        :param bool clean: Whether to clean the working tree. Defaults to ``True``.
        :param bool fetch: Whether to fetch remote. Defaults to ``True``.
        :param str rev: Optional revision to checkout. Only has an effect if clean
            is also set. If you don't want to clean, but still perform a checkout,
            call :meth:`~tbot.tc.git.GitRepository.checkout`.

        .. versionchanged:: 0.6.1
            ``GitRepository`` now fetches latest changes from remote by default.
        """
        super().__init__(target.host, target)
        if url is not None:
            # Clone and optionally clean repo
            already_cloned = self.host.test("test", "-d", self / ".git")
            if not already_cloned:
                self.host.exec0("mkdir", "-p", self)
                self.host.exec0("git", "clone", url, self)
            elif fetch:
                self.git0("fetch")

            if already_cloned:
                # Try resetting the branch to upstream, if the branch has an upstream
                if rev:
                    self.reset(rev, ResetMode.HARD)
                elif self.git("rev-parse", "@{u}")[0] == 0:
                    self.reset("@{u}", ResetMode.HARD)
                else:
                    self.reset("HEAD", ResetMode.HARD)
                if clean:
                    self.clean(untracked=True, noignore=True)


            else:
                if rev:
                    self.checkout(rev)
        else:
            # Assume a repo is supposed to already exist
            if not (self / ".git").exists():
                raise RuntimeError(f"{target} is not a git repository")
            if clean:
                self.reset("HEAD", ResetMode.HARD)
                self.clean(untracked=True, noignore=True)

            if rev:
                self.checkout(rev)

    def git(
        self, *args: typing.Union[str, linux.Path[H], linux.special.Special]
    ) -> typing.Tuple[int, str]:
        """
        Run a git subcommand.

        Behaves like calling ``git -C <path/to/repo> <*args>``.

        :param args: Command line parameters. First one should be a git subcommand.
        :rtype: tuple[int, str]
        :returns: Retcode and command output
        """
        return self.host.exec("git", "-C", self, *args)

    def git0(
        self, *args: typing.Union[str, linux.Path[H], linux.special.Special]
    ) -> str:
        """
        Run a git subcommand and ensure its retcode is zero.

        Behaves like calling ``git -C <path/to/repo> <*args>``.

        :param args: Command line parameters. First one should be a git subcommand.
        :rtype: str
        :returns: Command output
        :raises CommandFailedException: If the command exited with a non-zero return code
        """
        return self.host.exec0("git", "-C", self, *args)

    @property
    def head(self) -> str:
        """Return the current HEAD of this repo."""
        return self.git0("rev-parse", "HEAD").strip()

    @property
    def symbolic_head(self) -> str:
        """Return the current HEAD of this repo, as a symbolic if possible."""
        res = self.git("symbolic-ref", "--short", "--quiet", "HEAD")
        if res[0] == 0:
            return res[1].strip()
        else:
            return self.head

    def checkout(self, rev: str) -> None:
        """
        Checkout a revision or branch.

        :param str rev: Revision or branch name to be checked out.
        """
        self.git0("checkout", rev)

    def reset(self, rev: str, mode: ResetMode = ResetMode.MIXED) -> None:
        """
        Call ``git --reset``.

        :param str rev: Revision to reset to
        :param ResetMode mode: Reset mode to be used. Refer to the ``git-reset``
            man-page for more info.
        """
        self.git0("reset", mode.value, rev)

    def clean(
        self, force: bool = True, untracked: bool = False, noignore: bool = False
    ) -> None:
        """
        Call ``git clean``.

        :param bool force: ``-f``
        :param bool untracked: ``-d``
        :param bool noignore: ``-x``

        Refer to the ``git-clean`` man-page for more info.
        """
        options = "-"

        if force:
            options += "f"
        if untracked:
            options += "d"
        if noignore:
            options += "x"

        self.git0("clean", options if options != "-" else "")

    def add(self, f: linux.Path[H]) -> None:
        """Add a file to the index."""
        self.git0("add", f)

    @tbot.testcase
    def commit(self, msg: str, author: typing.Optional[str] = None) -> None:
        """
        Commit changes.

        :param str msg: Commit message
        :param str author: Optional commit author in the ``Author Name <email@address>``
            format.
        """
        additional: typing.List[str] = []
        if author is not None:
            additional += ["--author", author]

        self.git0("commit", *additional, "-m", msg)

    @tbot.testcase
    def am(self, patch: linux.Path[H]) -> int:
        """
        Apply one or multiple patches.

        :param linux.Path patch: Either a path to a `.patch` file or to a
            directory containing patch files.
        :rtype: int
        :returns: Number of patches applied
        """
        # Check if we got a single patch or a patchdir
        if self.host.test("test", "-d", patch):
            files = [
                linux.Path(self.host, p)
                for p in self.host.exec0("find", patch, "-name", "*.patch")
                .strip("\n")
                .split("\n")
            ]

            files.sort()

            for f in files:
                self.am(f)

            return len(files)
        else:
            try:
                self.git0("am", "-3", patch)
            except:  # noqa: E722
                self.git0("am", "--abort")
                raise

        return 1

    @tbot.testcase
    def apply(self, patch: linux.Path[H]) -> int:
        """
        Apply one or multiple patches to the working tree.

        :param linux.Path patch: Either a path to a `.patch` file or to a
            directory containing patch files.
        :rtype: int
        :returns: Number of patches applied

        .. versionadded:: 0.6.4
        """
        # Check if we got a single patch or a patchdir
        if self.host.test("test", "-d", patch):
            files = [
                linux.Path(self.host, p)
                for p in self.host.exec0("find", patch, "-name", "*.patch")
                .strip("\n")
                .split("\n")
            ]

            files.sort()

            for f in files:
                self.apply(f)

            return len(files)
        else:
            try:
                self.git0("apply", patch)
            except:  # noqa: E722
                self.git0("apply", "--abort")
                raise

        return 1

    @tbot.testcase
    def bisect(self, good: str, test: "typing.Callable[..., bool]") -> str:
        """
        Run a git bisect to find the commit that introduced an error.

        .. todo::

            Add back the bisect example.

        :param str good: A known good commit, the current head will be assumed as bad.
        :param test: A function to check the state of the current commit.  Should return
            ``True`` if it is good and ``False`` if it is bad.  An exception is interpreded
            as an unexpected error while checking.
        :rtype: str
        :returns: The first bad commit
        """

        # First check if good is good and bad is bad
        tbot.log.message("Trying current revision ...")
        if test(self):
            raise AssertionError("The current revision isn't actually bad!")

        current = self.symbolic_head
        self.checkout(good)
        tbot.log.message(f"Trying 'good' revision ({good}) ...")
        if not test(self):
            self.checkout(current)
            raise AssertionError("The 'good' revision isn't actually good!")
        self.checkout(current)

        # Do the bisect now
        try:
            self.git0("bisect", "start")
            self.git0("bisect", "bad")
            self.git0("bisect", "good", good)

            while True:
                current = self.head
                tbot.log.message(f"Trying commit {current} ...")

                success = test(self)
                if success:
                    self.git0("bisect", "good", current)
                    tbot.log.message(
                        f"Commit {current} is " + tbot.log.c("good").green + "."
                    )
                else:
                    self.git0("bisect", "bad", current)
                    tbot.log.message(
                        f"Commit {current} is " + tbot.log.c("BAD").red + "."
                    )

                # Check how many commits are remaining
                remaining = (
                    self.git0(
                        "bisect", "visualize", "--pretty=format:%H", linux.Pipe, "cat"
                    )
                    .strip()
                    .split("\n")
                )
                tbot.log.message(f"{len(remaining)} commits remaining ...")

                if len(remaining) == 1:
                    tbot.log.message(
                        "First bad commit is " + tbot.log.c(remaining[0]).yellow
                    )
                    return remaining[0]
        finally:
            self.git0("bisect", "reset")
