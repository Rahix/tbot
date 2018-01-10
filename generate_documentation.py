""" Build a markdown document of the tbot run """
import json
import math

OMIT_LINES = 6

def main():
    """ Main """
    log = json.load(open("log.json"))

    appendices = []

    def gen_md(msg):
        """ Generate markdown for a log message """
        # if msg['type'][0] == "testcase":
        #     if msg['type'][1] == "begin":
        #         name = msg['name'].replace('_', '\\_')
        #         return f"# Testcase: {name} #\n\n"
        if msg['type'][0] == "shell" and msg['show'] is True:
            string = f"""
```console
$ {msg['command']}
```
"""

            out = msg['output'][:-1]
            if out != "":
                output = msg['output'][:-1]
                output_lines = output.split('\n')
                if len(output_lines) > OMIT_LINES: # Truncate
                    lnum = math.floor(OMIT_LINES/2)
                    output = '\n'.join(output_lines[:lnum]) \
                        + f"\n... {len(output_lines) - lnum*2} lines omitted ...\n" \
                        + '\n'.join(output_lines[-lnum:])
                string += f"""
Example Output:

```text
{output}
```
"""

            return string
        elif msg['type'][0] == "doc":
            if msg['type'][1] == "text":
                return msg['text']
            elif msg['type'][1] == "appendix":
                appendices.append((msg['title'], msg['text']))
        return ""

    print("".join(map(gen_md, log)))
    print("\n# Appendix #\n\n")
    for title, text in appendices:
        print(f"## {title} ##\n{text}\n")

if __name__ == "__main__":
    main()
