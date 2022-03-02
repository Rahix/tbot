import site
import sys
from setuptools import setup

# This hack is necessary for --editable installs to work.
#
# Upstream Issue: https://github.com/pypa/pip/issues/7953
site.ENABLE_USER_SITE = "--user" in sys.argv[1:]

if __name__ == "__main__":
    setup()
