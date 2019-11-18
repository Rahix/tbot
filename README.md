<p align="center">
  <img src="Documentation/static/tbot-logo-header.png" alt="tbot" /><br />
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.6-blue.svg" alt="Python 3.6" /></a>
  <a href="http://mypy-lang.org/"><img src="http://www.mypy-lang.org/static/mypy_badge.svg" alt="Checked with mypy" /></a>
  <a href="https://github.com/ambv/black"><img src="https://img.shields.io/badge/code%20style-black-000000.svg" alt="Code style: black" /></a>
  <a href="https://travis-ci.org/Rahix/tbot"><img src="https://travis-ci.org/Rahix/tbot.svg?branch=master" alt="Build Status" /></a><br />
  Embedded Test/Automation Tool
</p>

**tbot** is a testing/automation tool that is focused on usage in embedded development.  At its core *tbot* just provides utilities for interaction with remote hosts/targets and an extensive library of routines that are common in embedded development/testing.

*tbot* aims to be a support for the developer while working on a project and without much modification also allow running tests in an automated setting (CI).

Most info about *tbot* can be found in its documentation at <https://tbot.tools>.  You can also join our mailing list at [lists.denx.de](https://lists.denx.de/listinfo/tbot).

---

## Use-cases
*tbot* can very easily support complex test architectures with many different hosts and boards involved.  As an example:

![tbot Architecture](Documentation/static/tbot.png)


## Installation
```bash
python3 setup.py install --user
```

If you haven't done it already, you need to add ``~/.local/bin`` to your ``$PATH``.


### Completions
*tbot* supports command line completions. Enable them by adding

```bash
source /path/to/tbot/completions.sh
```

to your ``.bashrc`` or equivalent.


## Example
Blinks a GPIO Led on your selected target.

```python
import contextlib
import typing
import time
import tbot
from tbot.machine import linux


@tbot.testcase
@tbot.with_linux
def blink(lnx, pin: int = 18) -> None:
    """Blink the led on pin ``pin``."""
    sys_gpio = lnx.fsroot / "sys/class/gpio"
    gpio_n = sys_gpio / f"gpio{pin}"
    try:
        lnx.exec0("echo", str(pin), linux.RedirStdout(sys_gpio / "export"))

        # Wait for the gpio pin to be initialized
        time.sleep(0.5)
        lnx.exec0("echo", "out", linux.RedirStdout(gpio_n / "direction"))
        for _ in range(5):
            lnx.exec0("echo", "1", linux.RedirStdout(gpio_n / "value"))
            time.sleep(0.5)
            lnx.exec0("echo", "0", linux.RedirStdout(gpio_n / "value"))
            time.sleep(0.5)
    finally:
        lnx.exec0("echo", str(pin), linux.RedirStdout(sys_gpio / "unexport"))
```

## Credits
* [fast-entry_points](https://github.com/ninjaaron/fast-entry_points)
* [paramiko](https://www.paramiko.org/)
* [termcolor2](https://pypi.org/project/termcolor2/)

## Contributing
Help is really appreciated!  Please take a look at *tbot*'s [contribution guidelines](CONTRIBUTING.md)
for more info.  If you are unsure about anything, please open an issue or consult
the mailing list first!

## License
tbot is licensed under the `GNU General Public License v3.0 or later`.  See [LICENSE](LICENSE) for more info.
