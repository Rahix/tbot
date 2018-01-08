""" Testcases for working with git """
import os
import tbot


@tbot.testcase
def clean_repo_checkout(tb, target=None, repo=None):
    """ Checkout a git repo if it does not exist yet and make sure there are
        no artifacts left from previous builds """
    if not tb.shell.shell_type[0] == "sh":
        raise "Need an sh shell"

    if target is None or repo is None:
        raise "No target dir or no repository supplied"

    tb.shell.exec0(f"mkdir -p {target}")
    if not tb.shell.exec(f"""\
test -d {os.path.join(target, '.git')}""")[0] == 0:
        tb.shell.exec0(f"""\
git clone {repo} {target}""")
    else:
        tb.shell.exec0(f"""\
cd {target}; git reset --hard; git clean -f -d""")
        tb.shell.exec0(f"""\
cd {target}; git pull""")


@tbot.testcase
def apply_git_patches(tb, gitdir=None, patchdir=None):
    """ Apply patchfiles inside patchdir onto the git repository in
        gitdir """
    if not tb.shell.shell_type[0] == "sh":
        raise "Need an sh shell"

    if gitdir is None or patchdir is None:
        raise "No gitdir or no patchdir supplied"

    patchfiles = tb.shell.exec0(f"""\
find {patchdir} -name '*.patch'""").split("\n")

    for patch in patchfiles:
        tb.shell.exec0(f"""\
cd {gitdir}; git am -3 {patch}""")
