"""
Tescase collector
-----------------
"""
import pathlib
import typing
import importlib.util
import enforce
import tbot

TBOT_TESTCASES: typing.Dict[str, typing.Callable] = dict()
TBOT_TESTCASES_CMDLINE: typing.Dict[str, typing.Callable] = dict()

def cmdline(f: typing.Callable) -> typing.Callable:
    """ Decorator for testcases that can be called from the commandline as well """
    #pylint: disable=global-statement
    global TBOT_TESTCASES_CMDLINE
    TBOT_TESTCASES_CMDLINE[f.__name__] = f
    return f

def testcase(f: typing.Callable) -> typing.Callable:
    """ Decorator for testcases """
    #pylint: disable=global-statement
    global TBOT_TESTCASES
    if f.__name__ in TBOT_TESTCASES:
        raise Exception(f"Duplicate testcase: {f.__name__}")
    enforce.config({
        "mode": "covariant",
    })
    wrapped = enforce.runtime_validation(f)
    TBOT_TESTCASES[f.__name__] = wrapped
    return wrapped


def get_testcases(paths: typing.Union[typing.List[str], typing.List[pathlib.Path], None] = None) \
        -> typing.Dict[str, typing.Callable]:
    """
    Collect all testcases from the directories
    specified in ``paths``

    :param paths: List of directories to search
    :returns: Collection of testcases
    """
    def walkdir(path):
        """ List all python files in a directory recusively """
        for f in path.iterdir():
            if f.suffix == ".py":
                yield f
            elif f.is_dir() and f.name != "__pycache__":
                for subfile in walkdir(f):
                    yield subfile

    if paths is None:
        paths = [pathlib.Path("tc")]
    sources: typing.List[pathlib.Path] = list()
    for path in paths:
        # skip nonexistent paths
        path = pathlib.Path(path) if not isinstance(path, pathlib.Path) else path
        if path.is_dir():
            sources += list(walkdir(path))

    for source in sources:
        module_spec = importlib.util.spec_from_file_location(source.stem, str(source))
        module = importlib.util.module_from_spec(module_spec)
        if isinstance(module_spec.loader, importlib.abc.Loader):
            module_spec.loader.exec_module(module)
            if "EXPORT" in module.__dict__:
                for k in module.__dict__["EXPORT"]:
                    tbot.tc.__dict__[k] = module.__dict__[k]
        else:
            raise Exception(f"Failed to load {source}")

    return TBOT_TESTCASES, TBOT_TESTCASES_CMDLINE
