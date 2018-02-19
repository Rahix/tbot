.. TBot configuration guide

TBot configuration
==================

TBot uses python for it's config. The configuration is divided into
3 parts, with each part overriding values set in the previous ones:

1. ``config/labs/<lab-name>.py``: The lab configuration, used to tell TBot about
   the lab host, how to login and where to find stuff
2. ``config/boards/<board-name>.py``: The board configuration, used to tell TBot
   about the board
3. ``config/tbot.py``: A configuration file containing default values, sometimes
   based on values that should be set by the previous configs (lab + board). For
   example, the value ``"tbot.builddir"`` will be set differently, depending on
   the name of the board which is currently used. (But only if it was not set by
   any other config previously, ``tbot.py`` should never override anything) To
   ensure this, use the following syntax::

       cfg["value"] = cfg["value", "default"]

Inside the testcases, the configuration is available as ``tb.config`` and values should
be accessed like directories in a filesystem but with ``.`` as a separator. For example,
use ``"tbot.workdir"`` to access the ``workdir`` value in the ``tbot`` sub config::

    a_dir_inside_workdir = tb.config["tbot.workdir"] / "dir-name"

By default, something like ``tb.config["..."]`` will raise an exception if the value was not
set in the config. If it is a value with a sane default, access it using::

    val = tb.config["...", "default"]

This will return the default value if the key does not exist in the configuration.

Another thing about configs is, that paths should always be ``pathlib`` paths to increase readability
of testcases. Use ``pathlib.Path`` for paths on the TBot host (eg ``"lab.keyfile"``) and
``pathlib.PurePosixPath`` for paths on the Lab host (eg ``"tbot.workdir"``).

Examples:
---------

Lab configuration
^^^^^^^^^^^^^^^^^

.. automodule:: config.labs.local
   :members:

Board configuration
^^^^^^^^^^^^^^^^^^^

.. automodule:: config.boards.taurus
   :members:

Available options:
------------------

Lab
^^^

::

    cfg["lab"] = {
        # Name of the lab, does not need to match file name
        "name": "local",
        # Hostname that tbot will ssh to
        "hostname": "localhost",
        # Optional port number
        "port": 22,
        # Username on that host
        "user": "me",
        # Keyfile is advised as to not have a cleartext copy
        # of the password in this file
        "keyfile": "/home/me/.ssh/id_rsa",
        # Use this, if you need password authentication instead
        "password": "hunter2",
    }

TBot
^^^^

::

    cfg["tbot"] = {
        # Where tbot should store it's files on the lab host
        # (This is not enforced in any way)
        "workdir": "/home/me/tbotdir",
    }

TFTP
^^^^

::

    cfg["tftp"] = {
        # Path to the tftp folder
        "rootdir": "/tftpboot",
        "boarddir": "boardname",
        "tbotsubdir": "tbot",
        # tbot assumes the following tftp folder structure:
        # <rootdir>/<boarddir>/<tbotsubdir>
        # rootdir and tbotsubdir are usually set inside the lab
        # config, boarddir is set in the board config

        # Alternatively you can set an entirely custom
        # tftp directory with the following option:
        # (Do not set this if you don't need it!)
        "directory": "/tftpboot/boardname/tbot",
    }

U-Boot
^^^^^^

::

    cfg["uboot"] = {
        # Where to fetch U-Boot from. Use a local mirror to reduce
        # network load
        "repository": "git://git.denx.de/u-boot.git",
        # A directory containing patches to be applied over the U-Boot tree
        "patchdir": pathlib.PurePosixPath("/home/hws/Documents/corvus_patches"),

        "test": {
            # Whether the lab host has virtualenv installed. If it doesn't,
            # it needs pytest (if you want to run the U-Boot python test suite)
            "use_venv": true,
            # Where to find board hooks for the U-Boot testsuite
            "hooks": pathlib.PurePosixPath("/home/hws/hooks/P2020"),
            # An optional config file for the testsuite
            "config": pathlib.PurePosixPath("/home/hws/data/u_boot_boardenv_P2020RDB_PC_NAND.py"),
            # Board name to be passed to test.py (usually the defconfig minus the "_defconfig")
            "boardname": "P2020RDB-PC_NAND",
            # Maximum number of fails before aborting, don't specify this if all test should be attempted
            "maxfail": 1,
        },

        # By default, TBot will attempt to build U-Boot in
        # cfg["tbot.workdir"] / "uboot-<boardname>"
        # This can be overridden by setting the following config option:
        # (Do not set this if you don't need it!)
        "builddir": pathlib.PurePosixPath("/path/to/build/dir"),
    }

Toolchains
^^^^^^^^^^

::

    cfg["toolchains"] = {
        # A sample toolchain available on this labhost. These will be referenced
        # in the board config
        "cortexa8hf-neon": {
            # The env script which will be sourced to enable this toolchain
            "env_setup_script" = "/path/to/sdk/environment-setup-cortexa8hf-neon-poky-linux-gnueabi",
        },
    }

Board
^^^^^

::

    cfg["board"] = {
        # Name of the board, does not need to match file name
        "name": "at91sam9g45",
        # Name of the toolchain to be used. Toolchains are defined
        # in the lab config
        "toolchain": "cortexa8hf-neon",
        # which U-Boot defconfig to use
        "defconfig": "corvus_defconfig",

        "power": {
            # Command to power on the board
            "on_command": "remote_power at91sam9g45 on",
            # Command to power off the board
            "off_command": "remote_power at91sam9g45 off",
        },

        "shell": {
            # Identifier for this shell
            "name": "connect_at91sam9g45",
            # Command to open a rlogin like shell to the board
            "command": "connect at91sam9g45",
            # U-Boot prompt to be expected (varies with defconfig)
            "prompt": "U-Boot> ",
        },
    }
