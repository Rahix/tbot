import sys
import importlib
import pathlib
import typing


def list_dir(d: pathlib.Path, recurse: bool = False) -> typing.Generator[pathlib.Path, None, None]:
    for f in d.iterdir():
        if recurse and f.is_dir() and f.name != "__pycache__":
            for subf in list_dir(f, recurse):
                yield subf
        if f.suffix == ".py":
            yield f


def get_file_list(
    dirs: typing.Iterable[pathlib.Path],
    files: typing.Iterable[pathlib.Path],
) -> typing.Generator[pathlib.Path, None, None]:
    builtins = pathlib.Path(__file__).parent / "builtin"
    for f in list_dir(builtins, True):
        yield f
    tcpy = pathlib.Path.cwd() / "tc.py"
    if tcpy.is_file():
        yield tcpy

    tcdir = pathlib.Path.cwd() / "tc"
    if tcdir.is_dir():
        for f in list_dir(tcdir):
            yield f

    for d in dirs:
        if d.is_dir():
            for f in list_dir(d):
                yield f
        else:
            if d.exists():
                raise NotADirectoryError(str(d))
            else:
                raise FileNotFoundError(str(d))

    for f in files:
        if f.is_file():
            yield f
        else:
            raise FileNotFoundError(str(f))


def load_module(p: pathlib.Path) -> importlib.types.ModuleType:
    default_sys_path = sys.path
    try:
        module_spec = importlib.util.spec_from_file_location(
            name=p.stem,
            location=str(p),
        )
        module = importlib.util.module_from_spec(module_spec)
        if not isinstance(module_spec.loader, importlib.abc.Loader):
            raise TypeError(f"Invalid module spec {module_spec!r}")
        sys.path = default_sys_path + [str(p.parent)]
        module_spec.loader.exec_module(module)
    except:
        raise
    finally:
        sys.path = default_sys_path

    return module


def collect_testcases(
    files: typing.Iterable[pathlib.Path],
) -> typing.Dict[str, typing.Callable]:
    testcases: typing.Dict[str, typing.Callable] = {}

    for f in files:
        try:
            module = load_module(f)

            for name, func in module.__dict__.items():
                if hasattr(func, "_tbot_testcase"):
                    if name in testcases:
                        raise Exception(f"{func.__module__!r}: A testcase named {name!r} already exists in {(testcases[name]).__module__!r}")
                    testcases[name] = func
        except:
            pass

    return testcases
