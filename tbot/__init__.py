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
import time
import functools
from tbot import log, log_event

from . import selectable
from .selectable import (
    acquire_lab,
    acquire_board,
    acquire_uboot,
    acquire_linux,
    acquire_local,
)

__all__ = (
    "selectable",
    "acquire_lab",
    "acquire_board",
    "acquire_uboot",
    "acquire_linux",
    "acquire_local",
    "testcase",
    "log",
    "log_event",
)

F = typing.TypeVar("F", bound=typing.Callable[..., typing.Any])


def testcase(tc: F) -> F:
    """
    Decorate a function to make it a testcase.

    **Example**::

        @tbot.testcase
        def foobar_testcase(x: str) -> int:
            return int(x, 16)
    """

    @functools.wraps(tc)
    def wrapped(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
        log_event.testcase_begin(tc.__name__)
        start = time.monotonic()
        try:
            result = tc(*args, **kwargs)
        except:  # noqa: E722
            log_event.testcase_end(tc.__name__, time.monotonic() - start, False)
            raise
        log_event.testcase_end(tc.__name__, time.monotonic() - start, True)
        return result

    setattr(wrapped, "_tbot_testcase", tc.__name__)
    return typing.cast(F, wrapped)


def named_testcase(name: str) -> typing.Callable[[F], F]:
    """
    Decorate a function to make it a testcase, but with a different name.

    The testcase's name is relevant for log-events and when calling
    it from the commandline.

    **Example**::

        @tbot.named_testcase("my_different_testcase")
        def foobar_testcase(x: str) -> int:
            return int(x, 16)

    (On the commandline you'll have to run ``tbot my_different_testcase`` now.)
    """

    def _named_testcase(tc: F) -> F:
        @functools.wraps(tc)
        def wrapped(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
            log_event.testcase_begin(name)
            start = time.monotonic()
            try:
                result = tc(*args, **kwargs)
            except:  # noqa: E722
                log_event.testcase_end(name, time.monotonic() - start, False)
                raise
            log_event.testcase_end(name, time.monotonic() - start, True)
            return result

        setattr(wrapped, "_tbot_testcase", name)
        return typing.cast(F, wrapped)

    return _named_testcase


flags: typing.Set[str] = set()
