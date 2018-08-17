import typing
import tbot
from tbot.machine import linux


H = typing.TypeVar("H", bound=linux.LinuxMachine)


class GitRepository(linux.Path[H]):
    pass


@tbot.testcase
def checkout(url: str, target: linux.Path[H], clean: bool = True, rev: typing.Optional[str] = None) -> GitRepository[H]:
    h = target.host

    already_cloned = h.exec("test", "-d", target / ".git")[0] == 0
    if not already_cloned:
        h.exec0("mkdir", "-p", target)
        h.exec0("git", "clone", url, target)

    if clean or not already_cloned:
        if rev:
            h.exec0("git", "-C", target, "checkout", rev)

    if clean and already_cloned:
        h.exec0("git", "-C", target, "reset", "--hard", "origin")
        h.exec0("git", "-C", target, "clean", "-fdx")

    return GitRepository(h, target)


@tbot.testcase
def am(git: GitRepository[H], patch: linux.Path[H]) -> int:
    h = git.host

    # Check if we got a single patch or a patchdir
    if h.exec("test", "-d", patch)[0] == 0:
        files = [
            linux.Path(h, p)
            for p
            in h.exec0("find", patch, "-name", "*.patch").strip("\n").split("\n")
        ]

        files.sort()

        for f in files:
            am(git, f)

        return len(files)
    else:
        try:
            h.exec0("git", "-C", git, "am", "-3", patch)
        except:
            raise
        else:
            h.exec0("git", "-C", git, "am", "--abort")

    return 0
