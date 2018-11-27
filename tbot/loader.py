# tbot, Embedded Automation Tool
# Copyright (C) 2018  Harald Seiler
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
import importlib
import pathlib
import typing
from termcolor2 import c


def list_dir(
    d: pathlib.Path, recurse: bool = True
) -> typing.Generator[pathlib.Path, None, None]:
    for f in d.iterdir():
        if recurse and f.is_dir() and f.name != "__pycache__":
            for subf in list_dir(f, recurse):
                yield subf
        if f.suffix == ".py":
            yield f


def get_file_list(
    dirs: typing.Iterable[pathlib.Path], files: typing.Iterable[pathlib.Path]
) -> typing.Generator[pathlib.Path, None, None]:
    builtins = pathlib.Path(__file__).parent / "tc" / "callable.py"
    if builtins.is_file():
        yield builtins
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
    import importlib.util

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
    testcases: typing.Dict[str, typing.Callable] = {}

    for f in files:
        try:
            module = load_module(f)

            for name, func in module.__dict__.items():
                if hasattr(func, "_tbot_testcase"):
                    if name in testcases:
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
            print(c("Warning").yellow.bold + f": Failed to load {f}", file=sys.stderr)

    return testcases
