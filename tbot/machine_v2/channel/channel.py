# tbot, Embedded Automation Tool
# Copyright (C) 2019  Harald Seiler
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

import abc
import typing

ChanIO = typing.TypeVar("ChanIO", bound="ChannelIO")


class ChannelClosedException(Exception):
    pass


class ChannelIO(typing.ContextManager):
    __slots__ = ()

    @abc.abstractmethod
    def write(self, buf: bytes) -> None:
        pass

    @abc.abstractmethod
    def read(self, max: int = -1, timeout: typing.Optional[float] = None) -> bytes:
        pass

    @abc.abstractmethod
    def close(self) -> None:
        pass

    @abc.abstractmethod
    def fileno(self) -> int:
        pass

    @property
    @abc.abstractmethod
    def closed(self) -> bool:
        pass

    def __enter__(self: ChanIO) -> ChanIO:
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:  # type: ignore
        self.close()


class Channel(typing.Generic[ChanIO]):
    __slots__ = ("c",)

    def __init__(self, channel_io: ChanIO) -> None:
        self.c = channel_io

    # Standard pexpect-like interface {{{
    def send(self, s: typing.Union[str, bytes]) -> None:
        s = s.encode("utf-8") if isinstance(s, str) else s
        self.c.write(s)

    def sendline(self, s: typing.Union[str, bytes] = "") -> None:
        s = s.encode("utf-8") if isinstance(s, str) else s
        # TODO: \n or \r?
        self.c.write(s + b"\r")

    def sendcontrol(self, c: str) -> None:
        assert len(c) == 1
        assert c.isalpha() or c == "@"

        self.c.write(bytes([ord(c) - 64]))

    def sendeof(self) -> None:
        raise NotImplementedError()

    def sendintr(self) -> None:
        self.sendcontrol("C")

    # TODO: Reading
    # pexpect-like }}}
