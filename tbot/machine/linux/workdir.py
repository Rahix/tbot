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

from . import path, linux_shell
from .path import H


class Workdir(path.Path[H]):
    _workdirs: "typing.Dict[typing.Tuple[linux_shell.LinuxShell, str], Workdir]" = {}

    def __init__(self) -> None:  # noqa: D107
        raise NotImplementedError(
            "You are probably using this wrong, please refer to the documentation."
        )

    @classmethod
    def static(cls, host: H, pathstr: str) -> "Workdir[H]":
        """
        Create a workdir in a static location, described by ``pathstr``.

        **Example**:

        .. code-block:: python

            with tbot.acquire_lab() as lh:
                workdir = linux.Workdir.static(lh, "/tmp/tbot-my-workdir")

        :param LinuxShell host: Machine where the workdir should be created
        :param str pathstr: Path for the workdir
        :rtype: tbot.machine.linux.Path
        :returns: A tbot path to the workdir which is now guaranteed to exist
        """
        key = (host, pathstr)
        try:
            return Workdir._workdirs[key]
        except KeyError:
            p = typing.cast(Workdir, path.Path(host, pathstr))
            host.exec0("mkdir", "-p", p)
            Workdir._workdirs[key] = p
            return p

    @classmethod
    def athome(cls, host: H, subdir: str) -> "Workdir[H]":
        """
        Create a workdir below the current users home directory.

        **Example**:

        .. code-block:: python

            with tbot.acquire_lab() as lh:
                # Use ~/.local/share/tbot-foo-dir
                workdir = linux.Workdir.athome(lh, ".local/share/tbot-foo-dir")

        tbot will query the ``$HOME`` environment variable for the location of
        the current users home directory.

        :param LinuxShell host: Machine where the workdir should be created
        :param str subdir: Subdirectory of the user's home where the workdir should be created
        :rtype: tbot.machine.linux.Path
        :returns: A tbot path to the workdir which is now guaranteed to exist
        """
        key = (host, subdir)
        try:
            return Workdir._workdirs[key]
        except KeyError:
            home = host.env("HOME")
            p = typing.cast(Workdir, path.Path(host, home) / subdir)
            host.exec0("mkdir", "-p", p)
            Workdir._workdirs[key] = p
            return p
