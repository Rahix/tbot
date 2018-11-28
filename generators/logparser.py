# tbot, Embedded Automation Tool
# Copyright (C) 2018  Harald Seiler
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

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
