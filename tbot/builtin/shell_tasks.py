""" Common shell operations """
import os
import tbot

@tbot.testcase
def setup_tftpdir(tb):
    """ Setup the tftp directory """
    if not tb.shell.shell_type[0] == "sh":
        raise "Need an sh shell"

    tftpdir = os.path.join(
        tb.config.get("tftp.rootdir"),
        tb.config.get("tftp.boarddir"),
        tb.config.get("tftp.tbotsubdir"))

    tb.shell.exec0(f"mkdir -p {tftpdir}", log_show=False)

    return tftpdir

@tbot.testcase
def cp_to_tftpdir(tb, name=None, dest_name=None, from_builddir=True):
    """ Copy a file into the tftp folder """
    if not tb.shell.shell_type[0] == "sh":
        raise "Need an sh shell"

    if name is None:
        raise "Trying to copy nothing"

    build_dir = os.path.join(
        tb.config.workdir,
        f"u-boot-{tb.config.board_name}")
    tftpdir = os.path.join(
        tb.config.get("tftp.rootdir"),
        tb.config.get("tftp.boarddir"),
        tb.config.get("tftp.tbotsubdir"))


    source_path = os.path.join(build_dir, name) if from_builddir is True else name
    dest_path = os.path.join(tftpdir, name if dest_name is None else dest_name)

    tb.shell.exec0(f"cp {source_path} {dest_path}")
