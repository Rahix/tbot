from tbot.machine import linux


class Gpio:
    def __init__(self, host: linux.LinuxShell, gpio_number: int):

        self.host = host
        self.gpio_number = gpio_number
        self._gpio_sysclass_path = self.host.fsroot / "sys/class/gpio"
        self._gpio_path = self._gpio_sysclass_path / f"gpio{self.gpio_number}"
        self._export()
        self._direction = self.get_direction()
        self._active_low = self.get_active_low()

    def _export(self) -> None:
        if not self._gpio_path.is_dir():
            (self._gpio_sysclass_path / "export").write_text(str(self.gpio_number))

    def _is_in_direction(self) -> bool:
        return self._direction == "in"

    def _is_active_low_off(self) -> bool:
        return self._active_low == "0"

    def set_direction(self, direction: str) -> None:
        assert direction in ["in", "out"], f"Unsupported GPIO direction: {direction!r}"
        if self._direction == direction:
            return

        (self._gpio_path / "direction").write_text(direction)
        self._direction = direction

    def set_active_low(self, value: bool) -> None:
        if value:
            (self._gpio_path / "active_low").write_text("1")
            self._active_low = "1"
        else:
            (self._gpio_path / "active_low").write_text("0")
            self._active_low = "0"

    def get_active_low(self) -> str:
        return (self._gpio_path / "active_low").read_text().strip()

    def get_direction(self) -> str:
        return (self._gpio_path / "direction").read_text().strip()

    def set_value(self, value: bool) -> None:
        if self._is_in_direction():
            raise Exception("Can't set a GPIO which is not an output")
        else:
            if value:
                if self._is_active_low_off():
                    (self._gpio_path / "value").write_text("1")

                else:
                    (self._gpio_path / "value").write_text("0")

            else:
                if self._is_active_low_off():
                    (self._gpio_path / "value").write_text("0")
                else:
                    (self._gpio_path / "value").write_text("1")

    def get_value(self) -> str:
        if self._is_in_direction():
            return (self._gpio_path / "value").read_text().strip()
        else:
            raise Exception("Can't get a value from a GPIO which is not an input")
