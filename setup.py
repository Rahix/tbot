""" TBot """
from setuptools import setup, find_packages

setup(name="tbot",
      version="0.2.1",
      packages=find_packages(),
      install_requires=["paramiko", "enforce"],
      entry_points={
          "console_scripts": ["tbot = tbot.main:main"],
      },
      package_data={'tbot': ['builtin/*.py', 'builtin/**/*.py']},
     )
