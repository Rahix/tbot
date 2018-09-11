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
    @classmethod
    def from_path(cls, p: linux.Path[H]) -> "GitRepository[H]":
        if not (p / ".git").exists():
            raise RuntimeError(f"{p} is not a git repository")
        return cls(p.host, p)

    @classmethod
    def clone(
        cls,
        url: str,
        target: linux.Path[H],
        clean: bool = True,
        rev: typing.Optional[str] = None,
    ) -> "GitRepository[H]":
        return checkout(url, target, clean, rev)

    def am(self, patch: linux.Path[H]) -> int:
        return am(self, patch)

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

    def commit(self, msg: str, author: typing.Optional[str] = None) -> None:
        additional: typing.List[str] = []
        if author is not None:
            additional += ["--author", author]

        self.git0("commit", *additional, "-m", msg)


@tbot.testcase
def checkout(
    url: str,
    target: linux.Path[H],
    clean: bool = True,
    rev: typing.Optional[str] = None,
) -> GitRepository[H]:
    h = target.host

    already_cloned = h.exec("test", "-d", target / ".git")[0] == 0
    if not already_cloned:
        h.exec0("mkdir", "-p", target)
        h.exec0("git", "clone", url, target)

    repo = GitRepository(h, target)

    if clean or not already_cloned:
        if rev:
            repo.checkout(rev)

    if clean and already_cloned:
        repo.reset("origin", ResetMode.HARD)
        repo.clean(untracked=True, noignore=True)

    return repo


@tbot.testcase
def am(git: GitRepository[H], patch: linux.Path[H]) -> int:
    h = git.host

    # Check if we got a single patch or a patchdir
    if h.exec("test", "-d", patch)[0] == 0:
        files = [
            linux.Path(h, p)
            for p in h.exec0("find", patch, "-name", "*.patch").strip("\n").split("\n")
        ]

        files.sort()

        for f in files:
            am(git, f)

        return len(files)
    else:
        try:
            h.exec0("git", "-C", git, "am", "-3", patch)
        except:  # noqa: E722
            h.exec0("git", "-C", git, "am", "--abort")
            raise

    return 0
