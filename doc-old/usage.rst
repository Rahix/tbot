.. TBot usage

Commandline Usage
=================

TBot
----

.. code-block:: text

    usage: tbot [-h] [-i] [-p PARAM] [-c CONFIG] [--confdir CONFDIR]
                [--labconfdir LABCONFDIR] [--boardconfdir BOARDCONFDIR] [-d TCDIR]
                [-l LOGFILE] [-v] [-q] [--list-testcases] [--list-labs]
                [--list-boards]
                lab board [testcase [testcase ...]]

    A test tool for embedded linux development

    positional arguments:
      lab                   name of the lab to connect to
      board                 name of the board to test on
      testcase              name of the testcase to run
                            (default: "uboot_checkout_and_build")

    optional arguments:
      -h, --help            show this help message and exit
      -i, --interactive     Ask for each command before executing it
      -s, --show            Show info about the selected testcases
      -p PARAM, --param PARAM
                            Set a testcase parameter. Argument must be of the form
                            <param-name>=<python-expression>. WARNING: Uses eval!
      -c CONFIG, --config CONFIG
                            Set a config value. Argument must be of the form
                            <option-name>=<python-expression>. WARNING: Uses eval!
      --confdir CONFDIR     Specify alternate configuration directory
                            (default: "config/")
      --labconfdir LABCONFDIR
                            Specify alternate lab config directory
                            (default: "config/labs/")
      --boardconfdir BOARDCONFDIR
                            Specify alternate board config directory
                            (default: "config/boards/")
      -d TCDIR, --tcdir TCDIR
                            Add a directory to the testcase search path. The
                            default search path contains TBot's builtin testcases
                            and, if it exists, a subdirectory in the current
                            working directory named "tc"
      -l LOGFILE, --logfile LOGFILE
                            Json log file name
                            (default: "log/<lab>-<board>-<run>.json")
      -v, --verbose         Increase verbosity
      -q, --quiet           Decrease verbosity
      --list-testcases      List all testcases
      --list-labs           List all labs
      --list-boards         List all boards

TBot Manager
------------

.. code-block:: text

    usage: tbot-mgr [-h] {new,init,del,add} ...

    Config manager for TBot

    positional arguments:
      {new,init,del,add}
        new               Create a new directory with TBot config files
                          usage: tbot-mgr new [-h] [-s] [-f] dirname

        init              Create TBot config files in the current directory
                          usage: tbot-mgr init [-h] [-s] [-f]

        del               Delete a board/lab
                          usage: tbot-mgr del [-h] {board,lab} <name>

        add               Add a new board/lab to the config in the current
                          directory
                          usage: tbot-mgr add [-h] {board,dummy-board,lab,dummy-lab,dummies} ...


    optional arguments:
      -h, --help          show this help message and exit
