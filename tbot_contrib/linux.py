import re
from typing import Dict

from tbot.machine import linux

_MEMINFO_RE = re.compile(r"^([^:]+):\s+(\d+)( kB)?$")


def meminfo(lnx: linux.LinuxShell) -> Dict[str, int]:
    """
    Extract information from ``/proc/meminfo``.

    This helper returns a dict with the values from ``/proc/meminfo``
    for use in testcases.  For example, this can be used to check certain
    memory limits are not violated.

    .. code-block:: python

        meminfo = tbot_contrib.linux.meminfo(lnx)
        # At least 1 GiB of memory available
        assert meminfo["MemAvailable"] >= 0x40000000

    .. versionadded:: 0.10.4
    """
    meminfo_str = (lnx.fsroot / "proc" / "meminfo").read_text()
    meminfo = {}
    for line in meminfo_str.strip().split("\n"):
        match = _MEMINFO_RE.match(line)
        assert match is not None, f"Unexpected line {line!r} in /proc/meminfo"
        value = int(match.group(2))
        if match.group(3) is not None:
            value *= 1024
        meminfo[match.group(1)] = value
    return meminfo
