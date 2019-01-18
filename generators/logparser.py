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

import json
import pathlib
import sys
import typing


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

Log = typing.Generator[LogEvent, None, None]


def logfile(filename: str) -> Log:
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


def from_argv() -> Log:
    """Read logfile from location specified on commandline."""
    try:
        filename = pathlib.Path(sys.argv[1])
        return logfile(str(filename))
    except IndexError:
        sys.stderr.write(
            f"""\
\x1B[1mUsage: {sys.argv[0]} <logfile>\x1B[0m
"""
        )
        sys.exit(1)
    except OSError:
        sys.stderr.write(
            f"""\
\x1B[31mopen failed!\x1B[0m
\x1B[1mUsage: {sys.argv[0]} <logfile>\x1B[0m
"""
        )
        sys.exit(1)


if __name__ == "__main__":
    for ev in from_argv():
        print(repr(ev))
