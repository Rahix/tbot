.. tbot configuration guide

tbot configuration
==================

tbot uses ``toml`` as a configuration format. The configuration is divided
into 3 parts, with each part overriding values set in the previous ones:

1. ``config/tbot.toml``: The main configuration file, used as the base
2. ``config/labs/<lab-name>.toml``: The lab configuration, used to tell tbot about
   the lab host, how to login and where to find stuff
3. ``config/boards/<board-name>.toml``: The board configuration, used to tell tbot
   about the board

Lab configuration
------------------

::

    [lab]
    # Name of the lab, does not need to match file name
    name = "local"
    # Hostname that tbot will ssh to
    hostname = "localhost"
    # Optional port number
    # port = 22
    # Username on that host
    user = "me"
    # Keyfile is advised as to not have a cleartext copy
    # of the password in this file
    keyfile = "/home/me/.ssh/id_rsa"
    # Use this, if you need password authentication instead
    # password = "hunter2"

    [tbot]
    # Where tbot should store it's files on the lab host
    workdir = "/home/me/tbotdir"

    [tftp]
    # Path to the tftp folder
    rootdir = "/tftpboot"
    # tbot assumes the following tftp folder structure:
    # <rootdir>/<boarddir>/<tbotsubdir>
    # rootdir and tbotsubdir are usually set inside the lab
    # config, boarddir is set in the board config
    tbotsubdir = "tbot"

    [uboot]
    # Where to fetch U-Boot from. Use a local mirror to reduce
    # network load
    repository = "git://git.denx.de/u-boot.git"
    # Whether the lab host has virtualenv installed. If it doesn't,
    # it needs pytest (if you want to run the U-Boot python test
    # suite)
    test_use_venv = true

    # A sample toolchain available on this labhost. These will be referenced
    # in the board config
    [toolchains."cortexa8hf-neon"]
    # The env script which will be sourced to enable this toolchain
    env_setup_script = "/path/to/sdk/environment-setup-cortexa8hf-neon-poky-linux-gnueabi"

Board configuration
-------------------

::

    [board]
    # Name of the board, does not need to match file name
    name = "at91sam9g45"
    # Name of the toolchain to be used. Toolchains are defined
    # in the lab config
    toolchain = "cortexa8hf-neon"
    # which U-Boot defconfig to use
    defconfig = "corvus_defconfig"

    [board.power]
    # Command to power on the board
    on_command = "remote_power at91sam9g45 on"
    # Command to power off the board
    off_command = "remote_power at91sam9g45 off"

    [board.shell]
    # Identifier for this shell
    name = "connect_at91sam9g45"
    # Command to open a rlogin like shell to the board
    command = "connect at91sam9g45"
    # U-Boot prompt to be expected
    prompt = "U-Boot> "

    [uboot]
    # Optional location of patches to be applied to U-Boot
    # after checkout
    patchdir = "/path/to/corvus_patches"
    # Path to a directory containing the hooks for the U-Boot
    # python test suite
    test_hooks = "/path/to/hooks/corvus"
    # Name of the board to be supplied to the U-Boot python
    # test suite
    test_boardname = "corvus"

    [tftp]
    # See labconfig for an explanation
    boarddir = "at91sam9g45"
