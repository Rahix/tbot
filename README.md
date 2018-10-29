# TBot ![Python 3.6](https://img.shields.io/badge/python-3.6-blue.svg) [![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/) [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

TBot is a testing/automation tool that is focused on usage in embedded development.
At its core TBot just provides utilities for interaction with remote hosts/targets
and an extensive library of routines that are common in embedded development/testing.

TBot aims to be a support for the developer while working on a project and without
much modification also allow running tests in an automated setting (CI).

Most info about TBot can be found in its [documentation](https://rahix.de/tbot).

![TBot Architecture](doc/_static/tbot.png)

*Note that the TBot and Lab host can be the same machine.  Same with Lab and Build host.*


## Installation
```bash
python3 setup.py install --user
```

Also, if you haven't done this already, you need to add ``~/.local/bin`` to your ``$PATH``.

### Completions
TBot supports command line completions. Enable them by adding

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
def blink(
    mach: typing.Optional[linux.LinuxMachine] = None,
    pin: int = 18,
) -> None:
    """Blink the led on pin ``pin``."""
    with contextlib.ExitStack() as cx:
        if mach is None:
            lh = cx.enter_context(tbot.acquire_lab())
            b = cx.enter_context(tbot.acquire_board(lh))
            lnx = cx.enter_context(tbot.acquire_linux(b))
        else:
            lnx = mach

        sys_gpio = linux.Path(lnx, "/sys/class/gpio")
        gpio_n = sys_gpio / f"gpio{pin}"
        try:
            lnx.exec0("echo", str(pin), stdout=sys_gpio / "export")

            # Wait for the gpio pin to be initialized
            time.sleep(0.5)
            lnx.exec0("echo", "out", stdout=gpio_n / "direction")
            for _ in range(5):
                lnx.exec0("echo", "1", stdout=gpio_n / "value")
                time.sleep(0.5)
                lnx.exec0("echo", "0", stdout=gpio_n / "value")
                time.sleep(0.5)
        finally:
            lnx.exec0("echo", str(pin), stdout=sys_gpio / "unexport")
```

## Credits

* [fast-entry_points](https://github.com/ninjaaron/fast-entry_points)
* [paramiko](https://www.paramiko.org/)
* [termcolor2](https://pypi.org/project/termcolor2/)
