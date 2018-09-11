import typing
import tbot
import enum
from tbot.machine import linux


H = typing.TypeVar("H", bound=linux.LinuxMachine)


class ResetMode(enum.Enum):
    SOFT = "--soft"
    MIXED = "--mixed"
    HARD = "--hard"
    MERGE = "--merge"
    KEEP = "--keep"


class GitRepository(linux.Path[H]):
    def __new__(
        cls,
        target: linux.Path[H],
        url: typing.Optional[str] = None,
        *,
        clean: bool = True,
        rev: typing.Optional[str] = None,
    ) -> "GitRepository[H]":
        # Casting madness required because parent defines __new__
        return typing.cast(
            "GitRepository",
            super().__new__(
                typing.cast(typing.Type[linux.Path[H]], cls), target.host, target
            ),
        )

    def __init__(
        self,
        target: linux.Path[H],
        url: typing.Optional[str] = None,
        *,
        clean: bool = True,
        rev: typing.Optional[str] = None,
    ) -> None:
        super().__init__(target.host, target)
        if url is not None:
            # Clone and optionally clean repo
            already_cloned = self.host.exec("test", "-d", self / ".git")[0] == 0
            if not already_cloned:
                self.host.exec0("mkdir", "-p", self)
                self.host.exec0("git", "clone", url, self)

            if clean and already_cloned:
                self.reset("origin", ResetMode.HARD)
                self.clean(untracked=True, noignore=True)

            if clean or not already_cloned:
                if rev:
                    self.checkout(rev)
        else:
            # Assume a repo is supposed to already exist
            if not (self / ".git").exists():
                raise RuntimeError(f"{target} is not a git repository")

    def git(
        self, *args: typing.Union[str, linux.Path[H], linux.special.Special]
    ) -> typing.Tuple[int, str]:
        return self.host.exec("git", "-C", self, *args)

    def git0(
        self, *args: typing.Union[str, linux.Path[H], linux.special.Special]
    ) -> str:
        return self.host.exec0("git", "-C", self, *args)

    def checkout(self, rev: str) -> None:
        self.git0("checkout", rev)

    def reset(self, rev: str, mode: ResetMode = ResetMode.MIXED) -> None:
        self.git0("reset", mode.value, rev)

    def clean(
        self, force: bool = True, untracked: bool = False, noignore: bool = False
    ) -> None:
        options = "-"

        if force:
            options += "f"
        if untracked:
            options += "d"
        if noignore:
            options += "x"

        self.git0("clean", options if options != "-" else "")

    def add(self, f: linux.Path[H]) -> None:
        self.git0("add", f)

    @tbot.testcase
    def commit(self, msg: str, author: typing.Optional[str] = None) -> None:
        additional: typing.List[str] = []
        if author is not None:
            additional += ["--author", author]

        self.git0("commit", *additional, "-m", msg)

    @tbot.testcase
    def am(self, patch: linux.Path[H]) -> int:
        # Check if we got a single patch or a patchdir
        if self.host.exec("test", "-d", patch)[0] == 0:
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

        return 0
