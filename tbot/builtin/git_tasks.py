"""
Testcases for working with git
------------------------------
"""
import os
import tbot


@tbot.testcase
def clean_repo_checkout(tb, target=None, repo=None):
    """
    Checkout a git repo if it does not exist yet and make sure there are
    no artifacts left from previous builds.

    :param target: Where to clone the repository to
    :param repo: Where the git repository can be found
    :returns: Nothing
    """
    assert tb.shell.shell_type[0] == "sh", "Need an sh shell"

    assert target is not None, "No target supplied"
    assert repo is not None, "No repository supplied"

    tb.log.doc_log(f"Checkout the git repository `{repo}`:\n")

    tb.shell.exec0(f"mkdir -p {target}")
    if not tb.shell.exec(f"""\
test -d {os.path.join(target, '.git')}""", log_show=False)[0] == 0:
        tb.shell.exec0(f"""\
git clone {repo} {target}""")
    else:
        tb.shell.exec0(f"""\
cd {target}; git reset --hard; git clean -f -d""", log_show=False)
        tb.shell.exec0(f"""\
cd {target}; git pull""", log_show=False)

        # Log a git clone for documentation generation
        event = tbot.logger.ShellCommandLogEvent(['sh', 'noenv'], f"""\
git clone {repo} {target}""", log_show=True)
        tb.log.log(event)
        event.finished(0)


@tbot.testcase
def apply_git_patches(tb, gitdir=None, patchdir=None):
    """
    Apply patchfiles inside patchdir onto the git repository in gitdir.

    :param gitdir: Path to the git repository
    :param patchdir: Path to the folder containing the patches
    :returns: Nothing
    """
    assert tb.shell.shell_type[0] == "sh", "Need an sh shell"

    assert gitdir is not None, "No gitdir supplied"
    assert patchdir is not None, "No patchdir supplied"

    tb.log.doc_log(f"Apply the patches in `{patchdir}` \
(Copies of the patch files can be found in the appendix of this document):\n")

    patchfiles = tb.shell.exec0(f"""\
find {patchdir} -name '*.patch'""", log_show=False).strip('\n').split("\n")

    # Make sure, we apply patches in the correct order
    patchfiles.sort()

    for patch in patchfiles:
        tb.shell.exec0(f"""\
cd {gitdir}; git am -3 {patch}""", log_show_stdout=False)
        patchfile = tb.shell.exec0(f"cat {patch}", log_show=False)
        tb.log.doc_appendix(f"Patch {patch.split('/')[-1]}", f"""```patch
{patchfile}
```
""")
