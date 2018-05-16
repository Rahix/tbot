#!/usr/bin/python3
"""
Generate a markdown documentation of the tbot run
-------------------------------------------------
This script will print out a markdown documentation
describing how to reproduce the exact steps that happend
during the run.
"""
import json
import math
import sys

OMIT_LINES = 6

def main():
    """ Generate a markdown documentation """

    try:
        log = json.load(open(sys.argv[1]))
    except: #pylint: disable=broad-except
        sys.stderr.write(f"""\
\x1B[1mUsage: {sys.argv[0]} <logfile>\x1B[0m
""")
        raise

    if log[-1]['success'] != True:
        sys.stderr.write("""\
\x1B[1;33mWARNING:\x1B[0m The TBot run that generated this logfile
did not finish successfully, the documentation
that will be generated might be wrong!
""")

    appendices = {}

    def gen_md(msg):
        """ Generate markdown for a log message """
        # if msg['type'][0] == "testcase":
        #     if msg['type'][1] == "begin":
        #         name = msg['name'].replace('_', '\\_')
        #         return f"# Testcase: {name} #\n\n"
        if msg['type'][0] == "shell" and msg['show'] is True:
            prompt = "$"
            if msg['type'][1] == "labhost":
                prompt = "bash$"
            elif msg['type'][1:3] == ["board", "uboot"]:
                prompt = "U-Boot>"
            elif msg['type'][1:3] == ["board", "linux"]:
                prompt = "board-bash$"

            string = f"""
```console
{prompt} {msg['command']}
"""

            out = msg['output'][:-1]
            if msg['show_stdout'] and out != "":
                output = msg['output'][:-1]
                output_lines = output.split('\n')
                if len(output_lines) > OMIT_LINES: # Truncate
                    lnum = math.floor(OMIT_LINES/2)
                    output = '\n'.join(output_lines[:lnum]) \
                        + f"\n... {len(output_lines) - lnum*2} lines omitted ...\n" \
                        + '\n'.join(output_lines[-lnum:])
                string += f"""{output}
"""
            string += """```
"""

            return string
        elif msg['type'][0] == "doc":
            if msg['type'][1] == "text":
                return msg['text']
            elif msg['type'][1] == "appendix":
                appendices[msg['title']] = msg['text']
        return ""

    print("".join(map(gen_md, log)))
    if appendices != {}:
        print("\n# Appendix #\n\n")
        for title, text in appendices.items():
            print(f"## {title} ##\n{text}\n")
    print("""
# Disclaimer #
> This documentation was generated automatically. The steps described here \
led to a successful build on our system. Please make changes to accomodate for \
differences in your system.""")

if __name__ == "__main__":
    main()
