""" Tescase collector """
import os
import importlib.util

TBOT_TESTCASES = dict()


def testcase(f):
    """ Decorator for testcases """
    #pylint: disable=global-statement
    global TBOT_TESTCASES
    if f.__name__ in TBOT_TESTCASES:
        raise f"Duplicate testcase: {f.__name__}"
    TBOT_TESTCASES[f.__name__] = f
    return f


def get_testcases(paths=None):
    """ Collect testcases """

    if paths is None:
        paths = ["tc"]
    sources = list()
    for path in paths:
        # skip nonexistant paths
        if os.path.isdir(path):
            sources += [os.path.join(path, p)
                        for p in os.listdir(path)
                        if p.split(".")[-1] == "py"]

    for source in sources:
        module_spec = importlib.util.spec_from_file_location("tc", source)
        module = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(module)

        # tc_list = [name for name in dir(module) if
        #            name[:5] == "task_" or
        #            name[:3] == "tc_" or
        #            name[:3] == "ts_"]

        # for tc in tc_list:
        #     if tc in testcases:
        #         raise Exception(f"Duplicate testcase: {tc}")
        #     testcases[tc] = eval("module." + tc)

    return TBOT_TESTCASES
