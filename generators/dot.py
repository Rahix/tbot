#!/usr/bin/env python3
# tbot, Embedded Automation Tool
# Copyright (C) 2018  Heiko Schocher, Harald Seiler
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

"""Generate a dot graph."""
import logparser

NODE_NUMBER = 0


def node(name: str) -> int:
    """Create a node."""
    global NODE_NUMBER

    print(f'{NODE_NUMBER} [shape=record, label="{name}", color="black"];')

    NODE_NUMBER += 1
    return NODE_NUMBER - 1


def connection(a: int, b: int, color: str) -> None:
    """Create a connection between two nodes."""
    print(f'{a} -> {b} [color="{color}"]')


def main() -> None:
    """Generate a dot graph."""

    log = logparser.from_argv()

    print("digraph tc_dot_output { rankdir=LR;")

    stack = [node("tbot")]
    for ev in log:
        if ev.type == ["tc", "begin"]:
            n = node(ev.data["name"])
            connection(stack[-1], n, "black")
            stack.append(n)
        elif ev.type == ["tc", "end"]:
            connection(stack.pop(), stack[-1], "green" if ev.data["success"] else "red")

    print("}")


if __name__ == "__main__":
    main()
