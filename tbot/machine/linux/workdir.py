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
                # Use ~/tbot-foo-dir
                workdir = linux.Workdir.athome(lh, "tbot-foo-dir")

        tbot will query the ``$HOME`` environment variable for the location of
        the current users home directory.
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

    @classmethod
    def xdg_data(cls, host: H, subdir: str) -> "Workdir[H]":
        """
        Create a workdir in ``$XDG_DATA_HOME`` (usually ``~/.local/share``).

        **Example**:

        .. code-block:: python

            with tbot.acquire_lab() as lh:
                # Use ~/.local/share/tbot-foo-dir
                workdir = linux.Workdir.xdg_data(lh, "tbot-foo-dir")
        """
        key = (host, subdir)
        try:
            return Workdir._workdirs[key]
        except KeyError:
            xdg_data_dir = None
            try:
                res = host.env("XDG_DATA_HOME")
                if res != "":
                    xdg_data_dir = path.Path(host, res)
            except Exception:
                pass

            if xdg_data_dir is None:
                xdg_data_dir = path.Path(host, host.env("HOME")) / ".local" / "share"

            p = typing.cast(Workdir, path.Path(host, xdg_data_dir) / subdir)
            host.exec0("mkdir", "-p", p)
            Workdir._workdirs[key] = p
            return p
