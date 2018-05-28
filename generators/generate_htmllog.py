#!/usr/bin/python3
"""
Generate an html log
--------------------
Create an html representation of the log,
using U-Boot's python test suite's html log
generator as a base
"""
import json
import sys
import pathlib
import string


def main():
    """ Generate an html log """

    try:
        filename = pathlib.Path(sys.argv[1])
        log = json.load(open(filename))
    except IndexError:
        sys.stderr.write(
            f"""\
\x1B[1mUsage: {sys.argv[0]} <logfile>\x1B[0m
"""
        )
        sys.exit(1)
    except json.JSONDecodeError:
        sys.stderr.write(
            f"""\
\x1B[31mInvalid JSON!\x1B[0m
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

    # pylint: disable=too-many-return-statements
    def gen_html(msg):
        """ Generate html for a log message """
        if msg["type"] == ["testcase", "begin"]:
            return f"""<div class="section block">
                         <div class="section-header block-header">
                           {msg['name']}
                         </div>
                         <div class="section-content block-content">
                           <div class="action">
                             <pre></pre>
                           </div>"""
        elif msg["type"] == ["testcase", "end"]:
            if msg["success"]:
                return f"""<div class="status-pass">
                             <pre>OK, Time: {msg['duration']:.2f}s</pre>
                           </div>
                         </div>
                       </div>"""
            if msg["fail_ok"]:
                return f"""<div class="status-xpass">
                             <pre>Fail expected, Time: {msg['duration']:.2f}s</pre>
                           </div>
                         </div>
                       </div>"""
            return f"""    <div class="status-fail">
                             <pre>FAIL, Time: {msg['duration']:.2f}s</pre>
                           </div>
                         </div>
                       </div>"""
        elif msg["type"][0] == "shell":
            shell_type = repr(tuple(msg["type"][1:]))
            command = repr(msg["command"])[1:-1]
            output = (
                msg["output"][:-1]
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
            )
            return f"""    <div class="block">
                             <div class="block-header">
                               {shell_type} {command}
                             </div>
                             <div class="block-content">
                               <pre>
{output}</pre>
                             </div>
                           </div>"""
        elif msg["type"] == ["board", "boot"]:
            output = (
                msg["log"]
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
            )
            return f"""    <div class="block">
                             <div class="block-header">
                               -&gt; Board boot log
                             </div>
                             <div class="block-content">
                               <pre>
{output}</pre>
                             </div>
                           </div>"""
        elif msg["type"][0] == "msg":
            output = (
                msg["text"]
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
            )
            return f"""    <div class="block">
                             <div class="block-header">
                               Message ({msg['type'][1]}):
                             </div>
                             <div class="block-content">
                               <pre>
{output}</pre>
                               <div class="level-{msg['type'][1]}" style="color: #aaa">
                                  <i>Loglevel: {msg['type'][1]}</i>
                               </div>
                             </div>
                           </div>"""
        elif msg["type"][0] == "exception":
            return f"""    <div class="block">
                             <div class="block-header">
                               Exception: {msg['name']}
                             </div>
                             <div class="block-content">
                               <pre>
{msg['trace']}</pre>
                             </div>
                           </div>"""
        elif (
            msg["type"] == ["tbot", "end"]
            or msg["type"] == ["tbot", "info"]
            or msg["type"][0] == "custom"
            or msg["type"][0] == "board"
            or msg["type"][0] == "doc"
        ):
            return ""

        raise Exception("unknown event %r" % (msg,))

    with open(pathlib.Path(__file__).parent / "template.html") as f:
        template_string = f.read()

    data = {
        "page_title": f"TBot log: {pathlib.Path(filename.stem)}",
        "content": "\n".join(map(gen_html, log)),
    }

    print(string.Template(template_string).safe_substitute(data))


if __name__ == "__main__":
    main()
