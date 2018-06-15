#!/usr/bin/python3
"""
Generate a JUnit XML file
-------------------------
.. warning::
   Because JUnit's design differs from TBot's a lot, the output is a little
   bit unusual. It should show all information but not always where you would
   expect to find it.
"""
import json
import sys
import typing
import junit_xml


class TestcaseExecution:
    """ A Testcase Execution """

    def __init__(self, name: str) -> None:
        self.name = name
        self.duration = 0
        self.sub_steps: typing.List[typing.Union[TestcaseExecution, ShellStep]] = []
        self.success = True
        self.exc = None
        self.trace = None


class ShellStep:
    """ A Shell command execution """

    def __init__(self, command: str, output: str) -> None:
        self.command = command
        self.output = output


def parse_log(
    log: typing.List[typing.Dict[str, typing.Any]]
) -> typing.List[TestcaseExecution]:
    """ Parse json log """
    toplevels = []

    stack = []
    exception = None
    for ev in log:
        ty = ev["type"]
        # timestamp = ev['time']

        if ty == ["testcase", "begin"]:
            name = ev["name"]

            cur = TestcaseExecution(name)

            stack.append(cur)
        elif ty == ["testcase", "end"]:
            name = ev["name"]
            duration = ev["duration"]
            success = ev["success"]
            fail_ok = ev["fail_ok"]

            cur = stack.pop()
            assert cur.name == name
            cur.duration = duration
            cur.success = success or fail_ok
            if not success and not fail_ok and isinstance(exception, tuple):
                cur.exc = exception[0]  # pylint: disable=unsubscriptable-object
                cur.trace = exception[1]  # pylint: disable=unsubscriptable-object
                exception = None

            if stack != []:
                stack[-1].sub_steps.append(cur)
            else:
                toplevels.append(cur)
        elif ty == ["exception"]:
            exception = (ev["name"], ev["trace"])
        elif ty[0] == "shell":
            command = ev["command"]
            output = ev["output"]

            stack[-1].sub_steps.append(ShellStep(command, output))

    return toplevels


def toplevel_to_junit(
    num: int, toplevel: TestcaseExecution
) -> typing.List[junit_xml.TestCase]:
    """ Convert a toplevel testcase to junit testcases """
    testcases: typing.List[junit_xml.TestCase] = []
    _, testcases = testcase_to_junit(
        f"{num:02} - {toplevel.name}", 0, toplevel.name, toplevel, True
    )
    return testcases


def testcase_to_junit(
    toplevel: str,
    i: int,
    cls_path: str,
    testcase: TestcaseExecution,
    is_toplevel: bool = False,
) -> typing.Tuple[int, typing.List[junit_xml.TestCase]]:
    """ Convert a testcase to junit testcases """
    testcases = []
    my_cls_path = cls_path if is_toplevel else f"{cls_path} -> {testcase.name}"
    tc = junit_xml.TestCase(
        f"99999 - Summary {testcase.name}",
        classname=f"{toplevel}.{i:05} - {my_cls_path}",
    )
    if not testcase.success:
        if testcase.exc is not None:
            tc.add_error_info(f'Testcase failed with "{testcase.exc}"', testcase.trace)
        else:
            tc.add_error_info(f"Testcase failed because of sub testcase failure")
    testcases.append(tc)
    old_i = i
    i += 1
    for step_id, step in enumerate(testcase.sub_steps):
        if isinstance(step, TestcaseExecution):
            tc = junit_xml.TestCase(
                f"{step_id:05} - Testcase: {step.name}",
                classname=f"{toplevel}.{old_i:05} - {my_cls_path}",
            )
            testcases.append(tc)
            i_new, testcases_new = testcase_to_junit(toplevel, i, my_cls_path, step)
            i = i_new
            testcases += testcases_new
        elif isinstance(step, ShellStep):
            tc = junit_xml.TestCase(
                f"{step_id:05} - Shell: {step.command}",
                classname=f"{toplevel}.{old_i:05} - {my_cls_path}",
                stdout=step.output,
            )
            testcases.append(tc)
    return i, testcases


def main() -> None:
    """ Generate a JUnit XML file """

    try:
        log = json.load(open(sys.argv[1]))
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

    toplevels = parse_log(log)
    testcases: typing.List[junit_xml.TestCase] = []
    for i, toplevel in enumerate(toplevels):
        testcases += toplevel_to_junit(i, toplevel)
    print(
        json.dumps(list(map(lambda x: f"{x.classname}", testcases)), indent=4),
        file=sys.stderr,
    )

    print(junit_xml.TestSuite.to_xml_string([junit_xml.TestSuite("TBot", testcases)]))


if __name__ == "__main__":
    main()
