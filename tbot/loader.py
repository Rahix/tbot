# tbot, Embedded Automation Tool
# Copyright (C) 2019  Harald Seiler
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import sys
import pathlib
import typing
import types
from termcolor2 import c


def list_dir(
    d: pathlib.Path, recurse: bool = True
) -> typing.Generator[pathlib.Path, None, None]:
    """
    List all files ending in ``.py`` inside ``d``.

    :param pathlib.Path d: Where to search
    :param bool recurse: Whether to recurse into subdirectories
    :rtype: pathlib.Path
    :returns: A generator for iterating over all python files
    """
    for f in d.iterdir():
        if recurse and f.is_dir() and f.name != "__pycache__":
            for subf in list_dir(f, recurse):
                yield subf
        if f.suffix == ".py":
            yield f


def get_file_list(
    env_dirs: typing.Iterable[pathlib.Path],
    dirs: typing.Iterable[pathlib.Path],
    files: typing.Iterable[pathlib.Path],
) -> typing.Generator[pathlib.Path, None, None]:
    """
    Find all files which should testcases should be read from.

    The order is the following:

    1. Builtin testcases, defined in ``tbot.tc.callable``,
       eg. ``interactive_linux``
    2. A file named ``tc.py`` in the current working directory
       (affected by ``-C``)
    3. All python files (recursively) from a folder named
       ``tc/`` in the current working directory
    4. Python files (non recursively) from all paths in the
       ``$TBOTPATH`` environment variable
    5. All python files (recursively) from folders specified
       using ``-T``.
    6. Files specified using ``-t``

    :param env_dirs: Paths from ``$TBOTPATH``
    :param dirs: Paths from ``-T``
    :param files: Paths from ``-t``
    :returns: Generator over all testcase files
    """
    # Builtin testcases
    builtins = pathlib.Path(__file__).parent / "tc" / "callable.py"
    if builtins.is_file():
        yield builtins

    # tc.py file
    tcpy = pathlib.Path.cwd() / "tc.py"
    if tcpy.is_file():
        yield tcpy

    # tc/ folder
    tcdir = pathlib.Path.cwd() / "tc"
    if tcdir.is_dir():
        for f in list_dir(tcdir):
            yield f

    # Paths from $TBOTPATH
    for d in env_dirs:
        if d.is_dir():
            for f in list_dir(d, recurse=False):
                yield f
        else:
            if d.exists():
                raise NotADirectoryError(str(d))
            else:
                raise FileNotFoundError(str(d))

    # Specified testcase folders
    for d in dirs:
        if d.is_dir():
            for f in list_dir(d):
                yield f
        else:
            if d.exists():
                raise NotADirectoryError(str(d))
            else:
                raise FileNotFoundError(str(d))

    # Specified testcase files
    for f in files:
        if f.is_file():
            yield f
        else:
            raise FileNotFoundError(str(f))


def load_module(p: pathlib.Path) -> types.ModuleType:
    """
    Load a python module from a path.

    :param pathlib.Path p: Path to ``<module>.py``
    :rtype: Module
    """
    import importlib.util
    import importlib.abc

    if not p.is_file():
        raise FileNotFoundError(f"The module {str(p)!r} does not exist")
    default_sys_path = sys.path
    try:
        module_spec = importlib.util.spec_from_file_location(
            name=p.stem, location=str(p)
        )
        module = importlib.util.module_from_spec(module_spec)
        if not isinstance(module_spec.loader, importlib.abc.Loader):
            raise TypeError(f"Invalid module spec {module_spec!r}")
        sys.path = default_sys_path + [str(p.parent)]
        module_spec.loader.exec_module(module)
    finally:
        sys.path = default_sys_path

    return module


def collect_testcases(
    files: typing.Iterable[pathlib.Path],
) -> typing.Dict[str, typing.Callable]:
    """
    Create a dict of all testcases found in the given files.

    Reads all files in order and finds all functions annotated with
    :func:`tbot.testcase`.  Will print a warning if two testcases
    have the same name.

    :param files: Iterator of files
    :returns: A mapping of names to testcases (functions)
    """
    testcases: typing.Dict[str, typing.Callable] = {}

    for f in files:
        try:
            module = load_module(f)

            for func in module.__dict__.values():
                name = getattr(func, "_tbot_testcase", None)
                if name is not None:
                    if name in testcases:
                        # If it already exists, check so we don't warn about the
                        # testcase being imported into another files global namespace
                        if testcases[name].__code__ is func.__code__:
                            continue

                        print(
                            c("Warning").yellow.bold + f": Duplicate testcase {name!r}",
                            file=sys.stderr,
                        )

                        def duplicate(*args: typing.Any, **kwargs: typing.Any) -> None:
                            files = "-/-"
                            paths = getattr(duplicate, "_tbot_files")
                            if paths is not None:
                                files = "\n  > ".join(map(str, paths))
                            raise RuntimeError(
                                c(
                                    f"The testcase {name!r} exists multiple times!"
                                ).yellow
                                + """
Please tighten your testcase paths or remove/rename them so this conflict can be resolved.

The testcase was defined in:
  > """
                                + files
                            )

                        tbot_files = getattr(testcases[name], "_tbot_files").copy()
                        tbot_files.append(f)
                        setattr(duplicate, "_tbot_files", tbot_files)

                        testcases[name] = duplicate
                    else:
                        func._tbot_files = [f]
                        testcases[name] = func
        except:  # noqa: E722
            import textwrap
            import traceback

            trace = textwrap.indent(traceback.format_exc(), "    ")
            print(
                c("Warning").yellow.bold + f": Failed to load {f}:\n{trace}",
                file=sys.stderr,
            )

    return testcases
