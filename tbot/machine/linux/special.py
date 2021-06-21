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
import shlex
import typing

import tbot.error
from . import linux_shell, path  # noqa: F401

H = typing.TypeVar("H", bound="linux_shell.LinuxShell")


class Special(typing.Generic[H]):
    __slots__ = ()

    @abc.abstractmethod
    def _to_string(self, host: H) -> str:
        raise tbot.error.AbstractMethodError()


class Raw(Special[H]):
    __slots__ = ("string",)

    def __init__(self, string: str) -> None:
        self.string = string

    def _to_string(self, _: H) -> str:
        return self.string


class _Stdio(Special[H]):
    __slots__ = ("file",)

    _both = False

    @property
    @abc.abstractmethod
    def _redir_token(self) -> str:
        raise tbot.error.AbstractMethodError()

    def __init__(self, file: path.Path[H]) -> None:
        self.file = file

    def _to_string(self, h: H) -> str:
        # The order of the redirects is important!  First, redirect stdout to a
        # file and then redirect stderr to stdout.  If this is switched around,
        # stderr will go to old stdout, before it was redirected (that is, the
        # terminal).
        result = self._redir_token + shlex.quote(self.file.at_host(h))

        if self._both:
            result += " 2>&1"

        return result


class RedirStdout(_Stdio[H]):
    _redir_token = ">"


class RedirStderr(_Stdio[H]):
    _redir_token = "2>"


class RedirBoth(_Stdio[H]):
    _redir_token = ">"
    _both = True


class AppendStdout(_Stdio[H]):
    _redir_token = ">>"


class AppendStderr(_Stdio[H]):
    _redir_token = "2>>"


class AppendBoth(_Stdio[H]):
    _redir_token = ">>"
    _both = True


class _Background(Special[H]):
    def __init__(
        self,
        *,
        stdout: typing.Optional[path.Path[H]] = None,
        stderr: typing.Optional[path.Path[H]] = None,
    ) -> None:
        self.stdout = stdout
        self.stderr = stderr

    def __call__(
        self,
        *,
        stdout: typing.Optional[path.Path[H]] = None,
        stderr: typing.Optional[path.Path[H]] = None,
    ) -> "_Background":
        return _Background(stdout=stdout, stderr=stderr)

    def _to_string(self, h: H) -> str:
        if self.stdout is not None and self.stderr is not None:
            if self.stdout == self.stderr:
                return f"1>{shlex.quote(self.stdout.at_host(h))} 2>&1 &"
            else:
                return f"1>{shlex.quote(self.stdout.at_host(h))} 2>{shlex.quote(self.stderr.at_host(h))} &"
        elif self.stderr is not None:
            return f"1>/dev/null 2>{shlex.quote(self.stderr.at_host(h))} &"
        elif self.stdout is not None:
            return f"2>/dev/null 1>{shlex.quote(self.stdout.at_host(h))} &"
        else:
            return "2>&1 1>/dev/null &"


class _Static(Special):
    __slots__ = ("string",)

    def __init__(self, string: str) -> None:
        self.string = string

    def _to_string(self, _: H) -> str:
        return self.string


AndThen = _Static("&&")
Background: _Background = _Background()
OrElse = _Static("||")
Pipe = _Static("|")
Then = _Static(";")
