from setuptools import setup, find_packages

setup(name="tbot",
      version="0.1.0",
      packages=find_packages(),
      entry_points={
          "console_scripts": [
              "tbot = tbot.main:main"
          ],
      },
     )
