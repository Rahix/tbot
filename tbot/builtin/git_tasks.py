"""
Testcases for working with git
------------------------------
"""
import typing
import pathlib
import tbot
from tbot import tc


@tbot.testcase
def git_dirty_checkout(
    tb: tbot.TBot,
    *,
    target: pathlib.PurePosixPath,
    repo: str,
    rev: typing.Optional[str] = None,
) -> tc.GitRepository:
    """
    Checkout a git repo if it does not exist yet, but do not touch it
    if it already exists

    :param pathlib.PurePosixPath target: Where to clone the repository to
    :param str repo: Where the git repository can be found
    :param rev: Revision to checkout (ie. commit-id or branch name)
    :returns: The git repository as a meta object for testcases that need a git
              repository
    :rtype: GitRepository
    """
    tb.shell.exec0(f"mkdir -p {target}")
    if not tb.shell.exec(f"test -d {target / '.git'}", log_show=False)[0] == 0:
        tb.shell.exec0(f"git clone {repo} {target}")
        if rev is not None:
            tb.shell.exec0(f"cd {target}; git checkout {rev}")
    else:
        tbot.log.debug("Repository already checked out ...")

        # Log a git clone for documentation generation
        stdout_handler = tbot.log_events.shell_command(
            machine=["labhost", "noenv"],
            command=f"git clone {repo} {target}" + ""
            if rev is None
            else f"; cd {target}; git checkout {rev}",
            show=True,
            show_stdout=False,
        )
        stdout_handler.dct["exit_code"] = 0

    return tc.GitRepository(target)


@tbot.testcase
def git_clean_checkout(
    tb: tbot.TBot,
    *,
    target: pathlib.PurePosixPath,
    repo: str,
    rev: typing.Optional[str] = None,
) -> tc.GitRepository:
    """
    Checkout a git repo if it does not exist yet and make sure there are
    no artifacts left from previous builds.

    :param pathlib.PurePosixPath target: Where to clone the repository to
    :param str repo: Where the git repository can be found
    :param rev: Revision to checkout (ie. commit-id or branch name)
    :returns: The git repository as a meta object for testcases that need a git
              repository
    :rtype: GitRepository
    """
    tbot.log.debug(f"Git checkout '{repo}' to '{target}'")

    tbot.log.doc(f"Checkout the git repository `{repo}`:\n")

    tb.shell.exec0(f"mkdir -p {target}")
    if not tb.shell.exec(f"test -d {target / '.git'}", log_show=False)[0] == 0:
        tb.shell.exec0(f"git clone {repo} {target}")
        if rev is not None:
            tb.shell.exec0(f"cd {target}; git checkout {rev}")
    else:
        tbot.log.debug("Repository already checked out, cleaning ...")
        tb.shell.exec0(
            f"cd {target}; git reset --hard origin; git clean -fdx", log_show=False
        )
        tb.shell.exec0(f"cd {target}; git pull", log_show=False)

        # Log a git clone for documentation generation
        stdout_handler = tbot.log_events.shell_command(
            machine=["labhost", "noenv"],
            command=f"git clone {repo} {target}",
            show=True,
            show_stdout=False,
        )
        stdout_handler.dct["exit_code"] = 0

        if rev is not None:
            tb.shell.exec0(f"cd {target}; git checkout {rev}")

    return tc.GitRepository(target)


@tbot.testcase
def git_apply_patches(
    tb: tbot.TBot, *, gitdir: tc.GitRepository, patchdir: pathlib.PurePosixPath
) -> None:
    """
    Apply patchfiles inside patchdir onto the git repository in gitdir.

    :param GitRepository gitdir: The git repositories meta object
    :param pathlib.PurePosixPath patchdir: Path to the folder containing the patches
    """

    tbot.log.debug(f"Applying patches in '{patchdir}' to '{gitdir}'")

    tbot.log.doc(
        f"Apply the patches in `{patchdir}` \
(Copies of the patch files can be found in the appendix of this document):\n"
    )

    patchfiles = (
        tb.shell.exec0(
            f"""\
find {patchdir} -name '*.patch'""",
            log_show=False,
        )
        .strip("\n")
        .split("\n")
    )

    # Make sure, we apply patches in the correct order
    patchfiles.sort()

    dbg_str = "\n    -> ".join(patchfiles)
    tbot.log.debug(f"The following patches were found:\n    -> {dbg_str}")

    for patch in patchfiles:
        tb.shell.exec0(
            f"""\
cd {gitdir}; git am -3 {patch}""",
            log_show_stdout=False,
        )
        patchfile = tb.shell.exec0(f"cat {patch}", log_show=False)
        tbot.log.doc_appendix(
            f"Patch {patch.split('/')[-1]}",
            f"""```patch
{patchfile}
```
""",
        )


@tbot.testcase
def git_bisect(
    tb: tbot.TBot,
    gitdir: tc.GitRepository,
    good: str,
    and_then: typing.Union[str, typing.Callable],
    params: typing.Optional[typing.Dict[str, typing.Any]] = None,
) -> typing.Optional[str]:
    """
    Perform a git bisect in the git repository at ``gitdir`` between HEAD (as the bad
    commit) and ``good``. Whether a commit is good or bad is decided by calling
    the ``and_then`` testcase.

    :param GitRepository gitdir: Meta object of the git repository that is supposed to be bisected
    :param str good: The good commit
    :param and_then: A testcase that decides whether a commit is good or bad
    :type and_then: str or typing.Callable
    :param dict params: Additional parameters for the ``and_then`` testcase
    :returns: The first bad commit
    :rtype: str
    """

    if params is None:
        params = dict()

    if and_then is None:
        raise Exception(
            "No test for deciding whether a commit is good or bad was provided"
        )

    assert isinstance(gitdir, pathlib.PurePosixPath)
    assert isinstance(good, str)

    bad_commit: typing.Optional[str] = None
    try:
        tb.shell.exec0(f"cd {gitdir}; git bisect start")
        tb.shell.exec0(f"cd {gitdir}; git bisect bad")
        tb.shell.exec0(f"cd {gitdir}; git bisect good {good}")

        def try_commit(
            tb: tbot.TBot,
            and_then: typing.Union[str, typing.Callable],
            params: typing.Dict[str, typing.Any],
        ) -> bool:
            """ Try a certain commit by calling the and_then testcase """
            try:
                tb.call(and_then, **params)
                success = True
            except Exception:  # pylint: disable=broad-except
                success = False

            if success:
                tb.shell.exec0(f"cd {gitdir}; git bisect good")
            else:
                tb.shell.exec0(f"cd {gitdir}; git bisect bad")
            return success

        while True:
            current = tb.shell.exec0(
                f"\
cd {gitdir}; git show | grep -E '^commit [0-9a-zA-Z]+$'"
            )[len("commit ") :].strip()
            tbot.log.message(f"Trying {current} ...")
            tb.call(try_commit, and_then=and_then, params=params)
            commits = tb.shell.exec0(
                f"\
cd {gitdir}; git bisect visualize | grep -E '^commit [0-9a-zA-Z]+$' --color=never"
            ).split("\n")[:-1]
            if len(commits) == 1:
                bad_commit = commits[0][len("commit ") :]
                tbot.log.message(f"First bad commit is {bad_commit}")
                break
    except Exception:
        raise
    finally:
        # Make sure we ALWAYS reset after bisecting
        tb.shell.exec0(f"cd {gitdir}; git bisect reset")
    return bad_commit
