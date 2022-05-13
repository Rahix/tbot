.. _installation:

Installation
============

Prerequisites
-------------
tbot supports running on Linux only.  Other UNIXes might work but are not tested.

tbot requires at least **Python 3.6**.  Any version older than that **will not
work**.

Installation
------------
1. Install tbot using

   .. code-block:: shell-session

      $ pip3 install -U --user git+https://github.com/rahix/tbot@v0.10.0

2. If you haven't done this already, you need to add ``~/.local/bin`` to your
   ``$PATH``.

3. tbot supports command line completions.  Install them with the following
   commands:

   .. code-block:: shell-session

      $ curl --create-dirs -L -o ~/.local/lib/tbot/completions.sh https://github.com/Rahix/tbot/raw/master/completions.sh
      $ echo "source ~/.local/lib/tbot/completions.sh" >>~/.bashrc

Troubleshooting
---------------
If the above did not work out of the box, take a look at the following list:

``tbot`` not found
^^^^^^^^^^^^^^^^^^
If your shell complains about the ``tbot`` command not existing, you have
probably forgotten to add ``~/.local/bin`` to your ``$PATH``.  Do this by
adding the following line to your ``.bashrc`` or equivalent:

.. code-block:: bash

   export PATH=~/.local/bin:$PATH

Installation successful, running ``tbot`` always throws an exception
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
If running ``tbot`` always throws an exception when run (even without any
arguments), try forcing a clean reinstallation:

.. code-block:: shell-session

   $ pip3 uninstall tbot
   $ # In the tbot source directory
   $ rm -rf build/ dist/ tbot.egg-info/
   $ python3 setup.py install --user

Paramiko
^^^^^^^^
Note that paramiko is no longer a required dependency.

If the installation does not work, most likely it is an error when
installing paramiko. I recommend installing paramiko through your distros
package manager (eg. ``python3-paramiko`` for Fedora). If your distros
version of paramiko is too old, you will then need to install paramiko
with pip (after installing the distro package):

.. code-block:: shell-session

   $ pip3 install --user paramiko
