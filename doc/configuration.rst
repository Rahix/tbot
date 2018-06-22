.. TBot configuration guide

Configuration
=============

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

Configuring your configuration
------------------------------

Because TBot's config is python, you can do all kinds of crazy with it. An example is making your
configuration configurable. For example, you might have a board that you want to either boot using
an nfs root filesystem or one from the internal MMC. To implement this, add a config option like the
following to your board config::

    # This line is necessary to ensure that a default value is set if none is defined elsewhere
    cfg["linux.use_nfs"] = cfg["linux.use_nfs", True]

    # Use it later on in your boot command:

    cfg["linux.boot_command"] = """\
    # Get kernel
    # Get dtb
    # Do other setup
    """ + ("""\
    setenv bootargs ${bootargs} root=/dev/nfs nfsroot=... nolock rw
    """ if cfg["linux.use_nfs"] else """\
    setenv bootargs ${bootargs} root=/dev/mmcblk0p1
    """) + """\
    bootm ${kern_addr} - ${dtb_addr}"""

Now you can either use this config like usual and use the default value (``True`` in this case)
or specify a custom one on the commandline::

    $ tbot <lab> <board> -c linux.use_nfs=False <testcase>

As with commandline testcase parameters, TBot will evaluate everything after the ``=`` as a python
expression using *eval*.

Examples
--------

**TODO**


.. _tbot-cfg-opts:

Available options
-----------------

.. highlight:: python
   :linenothreshold: 3

Lab
^^^

::

    cfg["lab"] = {
        # Name of the lab, does not need to match file name
        "name": "local",
        # Hostname of the labhost
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
        # Where tbot should store it's files on the labhost
        # (This is not enforced in any way)
        "workdir": "/home/me/tbotdir",
    }

TFTP
^^^^

::

    cfg["tftp"] = {
        # Path to the directory that is exported over TFTP
        "root": "/tftpboot",
        "boarddir": "boardname",
        "tbotsubdir": "tbot",
        # tbot assumes the following tftp folder structure:
        # <root>/<boarddir>/<tbotsubdir>
        # root and tbotsubdir are usually set inside the lab
        # config, boarddir is set in the board config

        # If you do not want to use this structure, you can
        # specify a custom direcory below "root":
        # (Do not set this if you don't need it!)
        "directory": "boardname/tbot",
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
        # which defconfig to use
        "defconfig": "corvus_defconfig",

        "shell": {
            # U-Boot prompt to be expected (varies with defconfig)
            "prompt": "U-Boot> ",
            # Timeout before stopping autoboot in seconds
            "timeout": 4,
        },

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

Linux
^^^^^

::

    cfg["linux"] = {
        # U-Boot command to boot Linux, may be multiple commands separated by '\n'
        "boot_command": "boot",
        "shell": {
            # Username for logging in on the board
            "username": "root",
            # Password for logging in on the board
            "password": "root",
            # Login prompt on the board, TBot will wait for this string
            # before sending the username
            "login_prompt": "login: ",
            # Time to wait after sending credentials
            "login_timeout": 1,
        },
    }

Build
^^^^^

::

    cfg["build"] = {
        # Default buildhost
        "default": "labhost",
        # Local buildhost for building on the labhost
        "local": "labhost",
        # A buildhost
        "labhost": {
            # SSH command for passwordless login on the buildhost
            "ssh_command": "ssh myself@localhost",
            # SCP command for passwordless file transfers to and from
            # the buildhost
            "scp_command": "scp",
            # SCP address to be appended before remote paths
            "scp_address": "myself@localhost",
            # Workdir on the buildhost where TBot can store it's files
            "workdir": pathlib.PurePosixPath("/tmp/tbot-build"),
            # Toolchains that are available on this host
            "toolchains": {
                # A sample toolchain available on this labhost. These will be referenced
                # in the board config
                "cortexa8hf-neon": {
                    # The env script which will be sourced to enable this toolchain
                    "env_setup_script" = "/path/to/sdk/environment-setup-cortexa8hf-neon-poky-linux-gnueabi",
                },
            },
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

        "power": {
            # Command to power on the board
            "on_command": "remote_power at91sam9g45 on",
            # Command to power off the board
            "off_command": "remote_power at91sam9g45 off",
        },

        "serial": {
            # Identifier for this connection
            "name": "connect_at91sam9g45",
            # Command to open a rlogin like connection to the board
            "command": "connect at91sam9g45",
            # Optional waittime after connecting but before powering on
            "connect_wait_time": 0.5,
        },
    }
