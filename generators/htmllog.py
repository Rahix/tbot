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

"""
Generate an html log.

Create an html representation of the log,
using U-Boot's python test suite's html log
generator as a base
"""
import sys
import re
import pathlib
import string
import logparser


def main() -> None:
    """Generate an html log."""

    log = logparser.from_argv()

    # pylint: disable=too-many-return-statements
    def gen_html(ev: logparser.LogEvent) -> str:
        """Generate html for a log message."""
        if ev.type == ["tc", "begin"]:
            return f"""\
                       <div class="section block">
                         <div class="section-header block-header">
                           {ev.data['name']}
                         </div>
                         <div class="section-content block-content">
                           """
        elif ev.type == ["tc", "end"]:
            if ev.data["success"]:
                return f"""\
                           <div class="status-pass">
                             <pre>OK, Time: {ev.data['duration']:.3f}s</pre>
                           </div>
                         </div>
                       </div>"""
            return f"""\
                           <div class="status-fail">
                             <pre>FAIL, Time: {ev.data['duration']:.3f}s</pre>
                           </div>
                         </div>
                       </div>"""
        elif ev.type[0] == "cmd":
            shell_type = f"[{ev.type[1]}]"
            command = ev.data["cmd"]
            try:
                output = (
                    ev.data["stdout"][:-1]
                    .replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                )
            except KeyError:
                output = "&lt;no output&gt;"
            return f"""\
                           <div class="block">
                             <div class="block-header">
                               {shell_type} {command}
                             </div>
                             <div class="block-content">
                               <pre>
{output}</pre>
                             </div>
                           </div>"""
        elif ev.type[0] == "board":
            idx = ["on", "off", "uboot", "linux"].index(ev.type[1])

            ev_name = [
                "BOARD POWER-ON",
                "BOARD POWER-OFF",
                "BOARD UBOOT START",
                "BOARD LINUX BOOT",
            ][idx]
            try:
                output = (
                    ev.data["output"]
                    .replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                )
            except KeyError:
                output = "<no output>"
            return f"""\
                           <div class="block">
                             <div class="block-header">
                               -&gt; <b>{ev_name}</b>
                             </div>
                             <div class="block-content">
                               <pre>
{output}</pre>
                             </div>
                           </div>"""
        elif ev.type[0] == "msg":
            output = (
                ev.data["text"]
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
            ) + "\n"
            first_line, message = output.split("\n", maxsplit=1)
            return f"""\
                           <div class="block">
                             <div class="block-header">
                               Message ({ev.type[1]}): {first_line}
                             </div>
                             <div class="block-content">
                               <pre>
{output}</pre>
                               <div class="level-{ev.type[1]}" style="color: #aaa">
                                  <i>Loglevel: {ev.type[1]}</i>
                               </div>
                             </div>
                           </div>"""
        elif ev.type[0] == "exception":
            return f"""\
                           <div class="block">
                             <div class="block-header">
                               Exception: {ev.data['name']}
                             </div>
                             <div class="block-content">
                               <pre>
{ev.data['trace']}</pre>
                             </div>
                           </div>"""
        elif (
            ev.type == ["tbot", "end"]
            or ev.type == ["tbot", "info"]
            or ev.type[0] == "custom"
            or ev.type[0] == "doc"
            or ev.type[0] == "__debug__"
        ):
            return ""

        raise Exception(f"Unknown event {ev!r}")

    with open(pathlib.Path(__file__).parent / "template.html") as f:
        template_string = f.read()

    data = {
        "page_title": f"tbot log: {pathlib.Path(pathlib.Path(sys.argv[1]).stem)}",
        "content": "\n".join(map(gen_html, log)),
    }

    page = string.Template(template_string).safe_substitute(data)

    ansi_escapes = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
    print(ansi_escapes.sub("", page))


if __name__ == "__main__":
    main()
