.. _installation:

Installation
============
Clone `tbot's repository <https://github.com/Rahix/tbot>`_, then
install tbot using

.. code-block:: shell-session

   $ python3 setup.py install --user

Also, if you haven't done this already, you need to add ``~/.local/bin`` to
your ``$PATH``.

.. note::
    *tbot* requires at least **Python 3.6**.  Any version older than that **will not work**.

You can install tbot's man-page using

.. code-block:: shell-session

   $ sudo python3 setup.py install_data

Completions
-----------
tbot supports command line completions. Enable them by adding

.. code-block:: bash

   source /path/to/tbot/completions.sh

to your ``.bashrc`` or equivalent.

Troubleshooting
---------------
If the above did not work out of the box, take a look at the following list:

Paramiko
^^^^^^^^
If the installation does not work, most likely it is an error when installing paramiko. I recommend installing
paramiko through your distros package manager (eg. ``python3-paramiko`` for Fedora). If your distros version of
paramiko is too old, you will then need to install paramiko with pip (after installing the distro package):

.. code-block:: shell-session

   $ pip3 install --user paramiko
