import testmachines

import tbot
import tbot_contrib.linux


def test_meminfo(tbot_context: tbot.Context) -> None:
    with tbot_context.request(testmachines.Localhost) as lo:
        meminfo = tbot_contrib.linux.meminfo(lo)
        # We can really expect more than 4 MiB of memory...
        assert meminfo["MemTotal"] > 0x400000
        # Let's hope this is something we can assume!
        assert meminfo.get("HardwareCorrupted", 0) == 0
