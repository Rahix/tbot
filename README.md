<p align="center">
  <img src="Documentation/static/tbot-logo-header.png" alt="tbot" /><br />
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.6-blue.svg" alt="Python 3.6" /></a>
  <a href="http://mypy-lang.org/"><img src="http://www.mypy-lang.org/static/mypy_badge.svg" alt="Checked with mypy" /></a>
  <a href="https://github.com/ambv/black"><img src="https://img.shields.io/badge/code%20style-black-000000.svg" alt="Code style: black" /></a>
  <a href="https://github.com/Rahix/tbot/actions"><img src="https://github.com/Rahix/tbot/workflows/tbot%20selftest%20CI/badge.svg" alt="tbot selftest CI" /></a><br />
  Embedded Test &amp; Automation Tool
</p>

Welcome to *tbot*!  *tbot* automates the development workflow for embedded
systems software.  This automation can then also be used for running tests
against real hardware, even in CI.

At its core, tbot is a library for interacting with remote hosts over various
connections.  For example, a target board can be accessed via serial console.
Or a TFTP-server via SSH.  tbot allows managing all these connections in
"parallel".  This means, you can orchestrate complex sequences of interaction
between them.

At the moment, the main focus of tbot lies in embedded Linux systems.  Support
for other systems is definitely intended to be added, too.

Most info about *tbot* can be found in its documentation at
<https://tbot.tools>.  You can also join our mailing list,
[tbot AT lists.denx.de](https://lists.denx.de/listinfo/tbot).

---

## Installation
```bash
pip3 install --user -U git+https://github.com/rahix/tbot@v0.10.4
```

If you haven't done it already, you need to add ``~/.local/bin`` to your ``$PATH``.


### Completions
*tbot* supports command line completions.  Install them with the following commands:

```bash
curl --create-dirs -L -o ~/.local/lib/tbot/completions.sh https://github.com/Rahix/tbot/raw/master/completions.sh
echo "source ~/.local/lib/tbot/completions.sh" >>~/.bashrc
```

## Usecase Examples
To show what tbot can help you with, here are a few simple example usecases:

#### Boot into Linux and run a few commands over serial console
```python
@tbot.testcase
def test_linux_simple():
    # request serial connection to Linux on the board
    with tbot.ctx.request(tbot.role.BoardLinux) as lnx:
        # now we can run commands
        lnx.exec0("uname", "-a")

        # or, for example, read a file from the target
        cmdline = (lnx.fsroot / "proc" / "cmdline").read_text()
```

#### Define custom bootloader commands to boot Linux
```python
class CustomBoardLinux(board.LinuxUbootConnector, board.LinuxBootLogin, linux.Bash):
    username = "root"
    password = None

    def do_boot(self, uboot):
        # set `autoload` env-var to false to prevent automatic DHCP-boot
        uboot.env("autoload", "false")

        # get an IP-address
        uboot.exec0("dhcp")

        # download kernel + initramfs from TFTP server
        loadaddr = 0x82000000
        uboot.exec0("tftp", hex(loadaddr), f"{tftp_ip}:{kernel_image_path}")

        # and boot it!
        return uboot.boot("bootm", hex(loadaddr))
```

#### Network speed test between a board and server
```python
@tbot.testcase
def test_ethernet_speed():
    with tbot.ctx() as cx:
        # boot into Linux on the board and acquire a shell-session
        lnx = cx.request(tbot.role.BoardLinux)

        # use ssh to connect to a network server to test against
        lh = cx.request(tbot.role.LabHost)

        # start iperf server
        with lh.run("iperf", "-s") as iperf_server:
            # and display its output while waiting for startup
            iperf_server.read_until_timeout(2)

            # now run iperf client on DUT
            tx_report = lnx.exec0("iperf", "-c", server_ip)

            # exit the server with CTRL-C
            tbot.log.message("Server Output:")
            iperf_server.sendcontrol("C")
            iperf_server.terminate0()
```

## Contributing
Help is really appreciated!  Please take a look at *tbot*'s [contribution
guidelines](CONTRIBUTING.md) for more info.  If you are unsure about anything,
please open an issue or consult the mailing list first!

## License
tbot is licensed under the `GNU General Public License v3.0 or later`.  See
[LICENSE](LICENSE) for more info.
