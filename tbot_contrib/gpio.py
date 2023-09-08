import time
from typing import Optional

from tbot.machine import linux


class Gpio:
    def __init__(
        self,
        host: linux.LinuxShell,
        gpio_number: int,
        *,
        sys_path: Optional[linux.Path] = None,
    ):
        """Initialize GPIO

        Raspberry Pi Model 2 and above use as gpio_number their BCM GPIO Numbers

        :param linux.LinuxShell host: Linux Shell
        :param int gpio_number: GPIO Number
        :param linux.Path sys_path: Path to the ``/sys/`` mountpoint if it differs
            from the default.

        .. versionchanged:: 0.10.6

            Added the ``sys_path`` parameter.
        """

        self.host = host
        self.gpio_number = gpio_number
        if sys_path is None:
            sys_path = self.host.fsroot / "sys"
        self._gpio_sysclass_path = sys_path / "class" / "gpio"
        self._gpio_path = self._gpio_sysclass_path / f"gpio{self.gpio_number}"
        self._export()
        self._direction = self.get_direction()

    def _export(self) -> None:
        """Exports GPIO"""
        if not self._gpio_path.is_dir():
            (self._gpio_sysclass_path / "export").write_text(str(self.gpio_number))

    def set_direction(self, direction: str) -> None:
        """Set Direction

        Sets direction to ``in`` or ``out``

        :param str direction: Direction to set
        """
        assert direction in ["in", "out"], f"Unsupported GPIO direction: {direction!r}"
        if self._direction == direction:
            return

        (self._gpio_path / "direction").write_text(direction)
        self._direction = direction

    def set_active_low(self, value: bool) -> None:
        """Set Active Low

        When Active Low is ``True``, the GPIO triggers on a ``LOW`` singnal, else on a ``HIGH`` signal

        :param bool value: Value
        """
        (self._gpio_path / "active_low").write_text("1" if value else "0")

    def get_active_low(self) -> bool:
        """Get Active Low

        Reads value and returns direction ``in`` or ``out``

        :rtype: bool
        :returns: Value
        """
        return (self._gpio_path / "active_low").read_text().strip() != "0"

    def get_direction(self) -> str:
        """Get Direction of GPIO

        Reads direction and returns direction ``in`` or ``out``

        :rtype: str
        :returns: Value
        """
        return (self._gpio_path / "direction").read_text().strip()

    def set_value(self, value: bool) -> None:
        """Set Value

        Sets value to ``HIGH`` and ``LOW``

        :param bool value: Value to set
        """
        if self._direction == "in":
            raise Exception("Can't set a GPIO which is not an output")
        (self._gpio_path / "value").write_text("1" if value else "0")

    def get_value(self) -> bool:
        """Get Value

        Reads value and returns value ``True`` or ``False``

        :rtype: bool
        :returns: Value
        """
        if not (self._direction == "in"):
            raise Exception("Can't get a value from a GPIO which is not an input")
        return (self._gpio_path / "value").read_text().strip() != "0"

    def pulse(self, on_time: float, off_time: Optional[float] = None) -> None:
        """Toggle GPIO

        Toggles GPIO Pin between ``HIGH`` and ``LOW``

        :param float on_time: Time GPIO is ``HIGH``
        :param float off_time: Time GPIO is ``LOW``. Defaults to ``on_time``

        .. versionadded:: 0.10.6
        """

        if off_time is None:
            off_time = on_time

        self.set_value(True)
        time.sleep(on_time)
        self.set_value(False)
        time.sleep(off_time)
