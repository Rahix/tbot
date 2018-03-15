#!/usr/bin/python3
""" Generate a human readable log """
import json
import sys

if __name__ == "__main__":

    try:
        LOG = json.load(open(sys.argv[1]))
    except: #pylint: disable=broad-except
        print(f"\x1B[1mUsage: {sys.argv[0]} <logfile>\x1B[0m\n")
        raise

    #pylint: disable=too-many-return-statements
    def gen_md(msg):
        """ Generate markdown for a log message """
        if msg['type'] == ["testcase", "begin"]:
            return f"""
## Starting testcase {msg['name']} ##
_Start time is {msg['time']}_
"""
        elif msg['type'] == ["testcase", "end"]:
            return f"""_Testcase {msg['name']} finished after {msg['duration']:.2f}s_
"""
        elif msg['type'][0] == "shell":
            cmd = repr(msg['command'])[1:-1]
            string = f"""Command ``{repr(tuple(msg['type'][1:]))} {cmd} `` \
returned `{msg['exit_code']}`."""
            output = msg['output'][:-1]
            if output != "":
                string += f""" Output:
```
{output}
```
"""
            else:
                string += "\n"
            return string
        elif msg['type'] == ["board", "poweroff"]:
            return f"""_Boardshell was cleaned up at {msg['time']}_
"""
        elif msg['type'] == ["tbotend"]:
            return f"""
## TBot finished with {'success' if msg['success'] else 'a failure'} ##
_Time: {msg['time']}_
"""
        elif msg['type'][0] == "doc":
            return ""
        elif msg['type'] == ["board", "boot"]:
            return f"""Board booted:

```
{msg['log']}
```
"""
        elif msg['type'][0] == "msg":
            return f"""Message ({msg['type'][1]}):
```
{msg['text']}
```
"""
        elif msg['type'][0] == "custom":
            return ""
        elif msg['type'][0] == "board":
            return ""

        raise Exception(f"Unknown event: {repr(msg['type'])}")

    print("# TBOT Log #")
    print("\n".join(map(gen_md, LOG)))
