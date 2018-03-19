.. tbot example workflow

Example Workflow
================

This is a description for an example of how you might make use of TBot.

Development
-----------

First, we checkout and prepare U-Boot for our board, in this case we are
going to use the P2020RDB-PCA board, which is known to TBot as ``p2020rdb``::

    tbot denx p2020rdb uboot_checkout_and_prepare -v

Next we want to change the configuration a little, we do this by switching
into the build environment::

    tbot denx p2020rdb interactive_build

This will open a shell in the U-Boot build directory on the labhost with the
toolchain already enabled, where we can change the configuration like this::

    make menuconfig

and then build U-Boot::

    make

Next, we get out of the build shell and install our new U-Boot on the board::

    tbot denx p2020rdb p2020rdb_install_uboot p2020rdb_check_install -v

``p2020rdb_install_uboot`` is for installing, ``p2020rdb_check_install`` will make
sure, we actually have installed it and nothing went wrong (at least nothing obvious).

Finally, we can connect to U-Boot with::

    tbot denx p2020rdb interactive_uboot

and test if our changes actually work. If they do, get back into the build shell,
and create a patch from the changes::

    make savedefconfig
    cp defconfig configs/P2020RDB-PC_NAND_defconfig
    git add configs/P2020RDB-PC_NAND_defconfig
    git commit -m "My great changes"
    git format-patch -1 HEAD

and copy that patch into some empty directory (``/home/hws/data/test_patches`` in this
example)::

    mv 0001-my-great-changes.patch /home/hws/data/test_patches/

Now, adjust the TBot configuration file for the P2020RDB-PCA board, by adding the patchdir::

    cfg["uboot.patchdir"] = pathlib.PurePosixPath("/home/hws/data/test_patches")

Rebuild and reinstall U-Boot and you should have your new changes available::

    tbot denx p2020rdb p2020rdb -v

Automation
----------
Now that we have a working version, we might want to continually make sure, that it works.
The standard way to do this is a CI, for example `buildbot <https://buildbot.net/>`_ or
`Jenkins <https://jenkins.io/>`_. To use TBot with either one, configure it to run the tbot
command for your testcase, in this case ``tbot denx p2020rdb p2020rdb -vvv``. It is advisable
to set the highest possible verbosity level to make it easier to understand where a failure
happened. Optionally, add one or more of the generators to automatically run as well, to get
a pretty version of the log (``generators/generate_htmllog.py``) or a documentation on how to
setup your board (``generators/generate_documentation.py``). For Jenkins, there is also a generator
to generate a JUnit XML file (``generators/junit.py``) that Jenkins can use to display the test results.
