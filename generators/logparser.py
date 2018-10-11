import typing
import json


class LogEvent:
    """Log Event."""

    __slots__ = ("type", "time", "data")

    def __init__(self, dct: typing.Dict[str, typing.Any]) -> None:
        """Create a new log event from raw json data."""
        self.type: typing.List[str] = dct["type"]
        self.time: float = dct["time"]
        self.data: typing.Dict[str, typing.Any] = dct["data"]

    def __repr__(self) -> str:
        return f"<LogEvent {self.type!r}@{self.time:.3f}: {self.data!r}>"


READ_SIZE = 8192


def logfile(filename: str) -> typing.Generator[LogEvent, None, None]:
    """Parse a logfile."""
    with open(filename, "r") as f:
        buf = f.read(READ_SIZE)

        decoder = json.JSONDecoder()
        while True:
            try:
                raw_ev, idx = decoder.raw_decode(buf)
            except json.JSONDecodeError:
                new = f.read(READ_SIZE)
                if new == "":
                    return
                else:
                    buf += new
                    buf = buf.lstrip()
                continue

            yield LogEvent(raw_ev)

            buf = buf[idx:].lstrip()


if __name__ == "__main__":
    import sys

    for ev in logfile(sys.argv[1]):
        print(repr(ev))
