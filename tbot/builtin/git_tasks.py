"""
Testcases for working with git
------------------------------
"""
import typing
import pathlib
import tbot

EXPORT = ["GitRepository"]

class GitRepository(pathlib.PurePosixPath):
    """ A meta object representing a git repository """
    pass

@tbot.testcase
def git_dirty_checkout(tb: tbot.TBot, *,
                       target: pathlib.PurePosixPath,
                       repo: str) -> GitRepository:
    """
    Checkout a git repo if it does not exist yet, but do not touch it
    if it already exists

    :param target: Where to clone the repository to
    :param repo: Where the git repository can be found
    :returns: The git repository as a meta object for testcases that need a git
              repository
    """
    tb.shell.exec0(f"mkdir -p {target}")
    if not tb.shell.exec(f"""\
test -d {target / '.git'}""", log_show=False)[0] == 0:
        tb.shell.exec0(f"""\
git clone {repo} {target}""")
    else:
        tb.log.log_debug("Repository already checked out ...")

        # Log a git clone for documentation generation
        event = tbot.logger.ShellCommandLogEvent(['sh', 'noenv'], f"""\
git clone {repo} {target}""", log_show=True)
        tb.log.log(event)
        event.finished(0)

    return GitRepository(target)

@tbot.testcase
def git_clean_checkout(tb: tbot.TBot, *,
                       target: pathlib.PurePosixPath,
                       repo: str) -> GitRepository:
    """
    Checkout a git repo if it does not exist yet and make sure there are
    no artifacts left from previous builds.

    :param target: Where to clone the repository to
    :param repo: Where the git repository can be found
    :returns: The git repository as a meta object for testcases that need a git
              repository
    """
    tb.log.log_debug(f"Git checkout '{repo}' to '{target}'")

    tb.log.doc_log(f"Checkout the git repository `{repo}`:\n")

    tb.shell.exec0(f"mkdir -p {target}")
    if not tb.shell.exec(f"""\
test -d {target / '.git'}""", log_show=False)[0] == 0:
        tb.shell.exec0(f"""\
git clone {repo} {target}""")
    else:
        tb.log.log_debug("Repository already checked out, cleaning ...")
        tb.shell.exec0(f"""\
cd {target}; git reset --hard; git clean -f -d""", log_show=False)
        tb.shell.exec0(f"""\
cd {target}; git pull""", log_show=False)

        # Log a git clone for documentation generation
        event = tbot.logger.ShellCommandLogEvent(['sh', 'noenv'], f"""\
git clone {repo} {target}""", log_show=True)
        tb.log.log(event)
        event.finished(0)

    return GitRepository(target)


@tbot.testcase
def git_apply_patches(tb: tbot.TBot, *,
                      gitdir: GitRepository,
                      patchdir: pathlib.PurePosixPath) -> None:
    """
    Apply patchfiles inside patchdir onto the git repository in gitdir.

    :param gitdir: The git repositories meta object
    :param patchdir: Path to the folder containing the patches
    """

    tb.log.log_debug(f"Applying patches in '{patchdir}' to '{gitdir}'")

    tb.log.doc_log(f"Apply the patches in `{patchdir}` \
(Copies of the patch files can be found in the appendix of this document):\n")

    patchfiles = tb.shell.exec0(f"""\
find {patchdir} -name '*.patch'""", log_show=False).strip('\n').split("\n")

    # Make sure, we apply patches in the correct order
    patchfiles.sort()

    dbg_str = '\n    -> '.join(patchfiles)
    tb.log.log_debug(f"The following patches were found:\n    -> {dbg_str}")

    for patch in patchfiles:
        tb.shell.exec0(f"""\
cd {gitdir}; git am -3 {patch}""", log_show_stdout=False)
        patchfile = tb.shell.exec0(f"cat {patch}", log_show=False)
        tb.log.doc_appendix(f"Patch {patch.split('/')[-1]}", f"""```patch
{patchfile}
```
""")

@tbot.testcase
def git_bisect(tb: tbot.TBot,
               gitdir: GitRepository,
               good: str,
               and_then: typing.Union[str, typing.Callable],
               params: typing.Optional[typing.Dict[str, typing.Any]] = None,
              ) -> typing.Optional[str]:
    """
    Perform a git bisect in the git repository at ``gitdir`` between HEAD (as the bad
    commit) and ``good``. Whether a commit is good or bad is decided by calling
    the ``and_then`` testcase.

    :param gitdir: Meta object of the git repository that is supposed to be bisected
    :param good: The good commit
    :param and_then: A testcase that decides whether a commit is good or bad
    :param params: Additional parameters for the ``and_then`` testcase
    :returns: The first bad commit
    """

    if params is None:
        params = dict()

    if and_then is None:
        raise Exception("No test for deciding whether a commit is good or bad was provided")

    assert isinstance(gitdir, pathlib.PurePosixPath)
    assert isinstance(good, str)

    bad_commit: typing.Optional[str] = None
    try:
        tb.shell.exec0(f"cd {gitdir}; git bisect start")
        tb.shell.exec0(f"cd {gitdir}; git bisect bad")
        tb.shell.exec0(f"cd {gitdir}; git bisect good {good}")


        def try_commit(tb: tbot.TBot,
                       and_then: typing.Union[str, typing.Callable],
                       params: typing.Dict[str, typing.Any]) -> bool:
            """ Try a certain commit by calling the and_then testcase """
            try:
                tb.call(and_then, **params)
                success = True
            except Exception: #pylint: disable=broad-except
                success = False

            if success:
                tb.shell.exec0(f"cd {gitdir}; git bisect good")
            else:
                tb.shell.exec0(f"cd {gitdir}; git bisect bad")
            return success

        while True:
            current = tb.shell.exec0(f"\
cd {gitdir}; git show | grep -E '^commit [0-9a-zA-Z]+$'")[len("commit "):].strip()
            tb.log.log_msg(f"Trying {current} ...")
            tb.call(try_commit, and_then=and_then, params=params)
            commits = tb.shell.exec0(f"\
cd {gitdir}; git bisect visualize | grep -E '^commit [0-9a-zA-Z]+$'") \
                .split("\n")[:-1]
            if len(commits) == 1:
                bad_commit = commits[0][len("commit "):]
                tb.log.log_msg(f"First bad commit is {bad_commit}")
                break
    except Exception:
        raise
    finally:
        # Make sure we ALWAYS reset after bisecting
        tb.shell.exec0(f"cd {gitdir}; git bisect reset")
    return bad_commit
