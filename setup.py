from setuptools import setup, find_packages

setup(
    name="tbot",
    version="0.6.0",
    packages=find_packages(include=("tbot", "tbot.*")),
    install_requires=["paramiko", "enforce", "termcolor2"],
    entry_points={
        "console_scripts": ["tbot = tbot.main:main", "tbot-mgr = tbot.mgr:main"]
    },
    package_data={"tbot": ["builtin/*.py", "builtin/**/*.py"]},
)
