.. _install:installation:

Installation
============
Clone `tbot's repository <https://github.com/Rahix/tbot>`_, then
install tbot using

::

    python3 setup.py install --user

Also, if you haven't done this already, you need to add ``~/.local/bin`` to
your ``$PATH``.

Completions
-----------
tbot supports command line completions. Enable them by adding

::

    source /path/to/tbot/completions.sh

to your ``.bashrc`` or equivalent.

Troubleshooting
---------------
If the above did not work out of the box, take a look at the following list:

Paramiko
^^^^^^^^
If the installation does not work, most likely it is an error when installing paramiko. I recommend installing
paramiko through your distros package manager (eg. ``python3-paramiko`` for Fedora). If your distros version of
paramiko is too old, you will then need to install paramiko with pip (after installing the distro package)::

    pip3 install --user paramiko
