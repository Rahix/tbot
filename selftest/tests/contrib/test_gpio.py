import testmachines

import tbot  # noqa: F401
import tbot_contrib.gpio  # noqa: F401


def test_gpio_smoke_in(tbot_context: tbot.Context) -> None:
    lo: testmachines.Localhost
    with tbot_context.request(testmachines.Localhost) as lo:
        fakesys = lo.workdir / "gpio-sys-in"
        if fakesys.is_dir():
            lo.exec0("rm", "-r", fakesys)
        fakesys.mkdir(parents=True, exist_ok=True)
        (fakesys / "class" / "gpio").mkdir(parents=True, exist_ok=True)
        (fakesys / "class" / "gpio" / "export").write_text("")

        gpio23 = fakesys / "class" / "gpio" / "gpio23"
        gpio23.mkdir()
        (gpio23 / "direction").write_text("in\n")
        (gpio23 / "value").write_text("1\n")

        pin = tbot_contrib.gpio.Gpio(lo, 23, sys_path=fakesys)
        assert pin.get_direction() == "in"

        assert pin.get_value()
        (gpio23 / "value").write_text("0\n")
        assert not pin.get_value()


def test_gpio_smoke_out(tbot_context: tbot.Context) -> None:
    lo: testmachines.Localhost
    with tbot_context.request(testmachines.Localhost) as lo:
        fakesys = lo.workdir / "gpio-sys-out"
        if fakesys.is_dir():
            lo.exec0("rm", "-r", fakesys)
        fakesys.mkdir(parents=True, exist_ok=True)
        (fakesys / "class" / "gpio").mkdir(parents=True, exist_ok=True)
        (fakesys / "class" / "gpio" / "export").write_text("")

        gpio42 = fakesys / "class" / "gpio" / "gpio42"
        gpio42.mkdir()
        (gpio42 / "direction").write_text("in\n")
        (gpio42 / "value").write_text("0\n")

        pin = tbot_contrib.gpio.Gpio(lo, 42, sys_path=fakesys)
        assert pin.get_direction() == "in"
        pin.set_direction("out")
        assert pin.get_direction() == "out"
        assert (gpio42 / "direction").read_text().strip() == "out"

        pin.set_value(True)
        assert (gpio42 / "value").read_text().strip() == "1"
        pin.set_value(False)
        assert (gpio42 / "value").read_text().strip() == "0"
