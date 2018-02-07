"""
Tescase collector
-----------------
"""
import os
import typing
import importlib.util

TBOT_TESTCASES: typing.Dict[str, typing.Callable] = dict()


def testcase(f: typing.Callable) -> typing.Callable:
    """ Decorator for testcases """
    #pylint: disable=global-statement
    global TBOT_TESTCASES
    if f.__name__ in TBOT_TESTCASES:
        raise Exception(f"Duplicate testcase: {f.__name__}")
    TBOT_TESTCASES[f.__name__] = f
    return f


def get_testcases(paths: typing.Optional[typing.List[str]] = None) \
        -> typing.Dict[str, typing.Callable]:
    if paths is None:
        paths = ["tc"]
    sources: typing.List[str] = list()
    for path in paths:
        # skip nonexistant paths
        if os.path.isdir(path):
            sources += [os.path.join(path, p)
                        for p in os.listdir(path)
                        if p.split(".")[-1] == "py"]

    for source in sources:
        module_spec = importlib.util.spec_from_file_location("tc", source)
        module = importlib.util.module_from_spec(module_spec)
        if isinstance(module_spec.loader, importlib.abc.Loader):
            module_spec.loader.exec_module(module)
        else:
            raise Exception(f"Failed to load {source}")

    return TBOT_TESTCASES
