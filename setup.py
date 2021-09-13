import typing
import pathlib
from setuptools import setup, find_packages
import fastentrypoints  # noqa: F401

tbot_dir = pathlib.Path(__file__).parent / "tbot"

about: typing.Dict[str, str] = {}
with open(tbot_dir / "__about__.py") as f:
    exec(f.read(), about)

setup(
    name=about["__title__"],
    version=about["__version__"],
    license="GPL-3.0-or-later",
    description=about["__summary__"],
    author=about["__author__"],
    author_email=about["__email__"],
    packages=find_packages(
        include=("tbot", "tbot.*", "tbot_contrib", "tbot_contrib.*")
    ),
    install_requires=["termcolor2"],
    extras_require={
        "paramiko": ["paramiko"],
    },
    entry_points={
        "console_scripts": ["tbot = tbot.main:main"]
    },
    data_files=[
        ("man/man1", ["Documentation/tbot.1"]),
    ],
    package_data={
        "tbot": ["py.typed"],
        "tbot_contrib": ["py.typed"],
    },
)
