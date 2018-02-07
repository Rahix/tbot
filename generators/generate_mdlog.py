#!/usr/bin/python3
""" Generate a human readable log """
import json

if __name__ == "__main__":

    LOG = json.load(open("log.json"))

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
        elif msg['type'] == ["boardshell_cleanup"]:
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
            return f""" Board booted:

```
{msg['log']}
```
"""
        elif msg['type'][0] == "custom":
            return ""

        raise Exception(f"Unknown event: {repr(msg['type'])}")

    print("# TBOT Log #")
    print("\n".join(map(gen_md, LOG)))
