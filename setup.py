from setuptools import setup, find_packages

setup(name="tbot",
      version="0.1.0",
      packages=find_packages(),
      requires=["paramiko", "argcomplete", "enforce"],
      entry_points={
          "console_scripts": ["tbot = tbot.main:main"],
      },
      package_data={'tbot': ['builtin/*.py', 'builtin/**/*.py']},
     )
