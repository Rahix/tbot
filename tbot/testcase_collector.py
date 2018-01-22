""" Tescase collector """
import os
import importlib.util

TBOT_TESTCASES = dict()


def testcase(f):
    """ Decorator for testcases """
    #pylint: disable=global-statement
    global TBOT_TESTCASES
    if f.__name__ in TBOT_TESTCASES:
        raise Exception(f"Duplicate testcase: {f.__name__}")
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

    return TBOT_TESTCASES
