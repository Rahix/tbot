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

import typing
from tbot import log, log_event

from . import selectable
from .selectable import (
    acquire_lab,
    acquire_board,
    acquire_uboot,
    acquire_linux,
    acquire_local,
)
from .decorators import testcase, named_testcase, with_lab, with_uboot, with_linux

__all__ = (
    "selectable",
    "acquire_lab",
    "acquire_board",
    "acquire_uboot",
    "acquire_linux",
    "acquire_local",
    "log",
    "log_event",
    "testcase",
    "named_testcase",
    "with_lab",
    "with_uboot",
    "with_linux",
)

flags: typing.Set[str] = set()


class SkipException(Exception):
    """
    Exception to be used when a testcase is skipped.

    Raising a :py:class:`SkipException` will be caught in the
    :py:func:`tbot.testcase` decorator and the testcase will return ``None``.
    This might violate the type-annotations so it should only be used if
    calling code can deal with a testcase returning ``None``.
    """

    pass


def skip(reason: str) -> typing.NoReturn:
    """
    Skip this testcase.

    A skipped testcase will return ``None`` instead of whatever type it would
    return normally.  This might not make sense for certain testcases and might
    violate the type-annotation.  *Only use it, if it really makes sense!*

    **Example**:

    .. code-block:: python

        @tbot.testcase
        @tbot.with_lab
        def test_something(lh) -> None:
            p = lh.fsroot / "dev" / "somedevice"

            if not p.is_char_device():
                tbot.skip("somedevice not present on this host")

            ...
    """
    raise SkipException(reason)
