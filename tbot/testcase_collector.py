"""
Tescase collector
-----------------
"""
import sys
import pathlib
import typing
import itertools
import importlib.util
import enforce
import tbot

TBOT_TESTCASES: typing.Dict[str, typing.Callable] = dict()

F = typing.TypeVar("F", bound=typing.Callable)


def testcase(f: F) -> F:
    """ Decorator for testcases """
    # pylint: disable=global-statement
    global TBOT_TESTCASES
    if f.__name__ in TBOT_TESTCASES:
        raise Exception(f"Duplicate testcase: {f.__name__}")
    enforce.config({"mode": "covariant"})
    wrapped = enforce.runtime_validation(f)
    TBOT_TESTCASES[f.__name__] = wrapped
    return f


def get_testcases(
    paths: typing.Union[typing.List[str], typing.List[pathlib.Path], None] = None
) -> typing.Dict[str, typing.Callable]:
    """
    Collect all testcases from the directories
    specified in ``paths``

    :param paths: List of directories to search
    :returns: Collection of testcases
    """

    def walkdir(path: pathlib.Path) -> typing.Generator[pathlib.Path, None, None]:
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

    export_sources = (source for source in sources if source.stem.endswith("_exports"))
    normal_sources = (
        source for source in sources if not source.stem.endswith("_exports")
    )
    # Keep the original path for restoring
    old_sys_path = sys.path
    # First load export sources then continue with normal
    for source in itertools.chain(export_sources, normal_sources):
        module_spec = importlib.util.spec_from_file_location(
            name=source.stem, location=str(source)
        )
        module = importlib.util.module_from_spec(module_spec)
        if isinstance(module_spec.loader, importlib.abc.Loader):
            sys.path = old_sys_path + [str(source.parent)]
            module_spec.loader.exec_module(module)
            sys.path = old_sys_path
            # Load exports
            if source.stem.endswith("_exports") and "EXPORT" in module.__dict__:
                for k in module.__dict__["EXPORT"]:
                    tbot.tc.__dict__[k] = module.__dict__[k]
        else:
            raise Exception(f"Failed to load {source}")

    return TBOT_TESTCASES
