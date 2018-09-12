from setuptools import setup, find_packages
import tbot.fastentrypoints  # noqa: F401

setup(
    name="tbot",
    version="0.6.0-pre02",
    packages=find_packages(include=("tbot", "tbot.*")),
    install_requires=["paramiko", "termcolor2"],
    entry_points={
        "console_scripts": ["tbot = tbot.main:main", "tbot-mgr = tbot.mgr:main"]
    },
    package_data={"tbot": ["builtin/*.py", "builtin/**/*.py"]},
)
