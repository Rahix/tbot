#!/usr/bin/env python3
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

"""Print all ["msg", ...] log events."""
import logparser


def main() -> None:
    """Main."""
    events = logparser.from_argv()

    for ev in events:
        if ev.type[0] == "msg":
            print(ev.data["text"])
            print()


if __name__ == "__main__":
    main()
