import tbot
from tbot.machine import linux
from tbot.tc import shell
from tbot_contrib import utils


@tbot.testcase
def swupdate_update_web(
    lh: linux.LinuxShell, swu_file: linux.Path, target_ip: str, timeout: int = 300
) -> None:
    """
    Upload an ``.swu`` file to a running swupdate server.

    :param linux.LinuxShell lh: The lab-host from where to initiate the update.
    :param linux.Path swu_file: Path to the ``.swu`` file (on the lab-host or
        locally).
    :param str target_ip: IP-Address of the target host.
    :param int timeout: Timeout.
    """
    with tbot.ctx.request(tbot.role.LocalHost) as lo:
        script_path = lh.workdir / "tbot_swupdate_web.py"
        swu_path = lh.workdir / "image.swu"
        script_source = linux.Path(lo, __file__).parent / "swupdate_script.py"

        if not utils.hashcmp(script_source, script_path):
            shell.copy(script_source, script_path)
        if not utils.hashcmp(swu_file, swu_path):
            shell.copy(swu_file, swu_path)
        lh.exec0("python3", script_path, swu_path, target_ip, str(timeout))
