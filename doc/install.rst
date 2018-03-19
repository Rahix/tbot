.. TBot installation

Installation
============
Clone the `TBot repository <https://gitlab.denx.de/HaraldSeiler/tbot>`_, then
install TBot using

::

    python3 setup.py install --user

Also, if you haven't done this already, you need to add ``~/.local/bin`` to
your ``$PATH``.

Completions
-----------
TBot supports command line completions. Enable them by adding

::

    eval "$(register-python-argcomplete tbot)"

to your ``.bashrc`` or equivalent.

Development
-----------
If you intend to work on TBot itself, you can install it in development mode::

    python3 setup.py develop --user

This does not install TBot like usual, but symlinks the installation to the repository,
so any changes you make are instantly available, without the need of reinstalling every
time.
