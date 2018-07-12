.. TBot installation

Installation
============
Clone the `TBot repository <https://gitlab.denx.de/HaraldSeiler/tbot>`_, then
install TBot using

::

    python3 setup.py install --user

Also, if you haven't done this already, you need to add ``~/.local/bin`` to
your ``$PATH``.

Troubleshooting
---------------
If the installation does not work, most likely it is an error when installing paramiko. I recommend installing
paramiko through your distros package manager (eg. ``python3-paramiko`` for Fedora). If your distros version of
paramiko is too old, you will then need to install paramiko with pip (after installing the distro package)::

    pip3 install --user paramiko

Completions
-----------
TBot supports command line completions. Enable them by adding

::

    source /path/to/tbot/completions.sh

to your ``.bashrc`` or equivalent.

Development
-----------
If you intend to work on TBot itself, you can install it in development mode::

    python3 setup.py develop --user

This does not install TBot like usual, but symlinks the installation to the repository,
so any changes you make are instantly available, without the need of reinstalling every
time.
