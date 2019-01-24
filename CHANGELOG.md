# Changelog

## [Unreleased]
### Added
- Read commandline arguments from files:  You can now specify a file using
  `@filename` and each line from that file will be interpreted as a commandline
  argument.
- A man-page: `doc/tbot.1`!
- `tbot.named_testcase`: Define testcases with a different name in log-files
  than the function name.  The motivation is to reduce name ambiguity
  (e.g. `uboot.build` and `linux.build` would both be called `build` in the
  log).  This also affects the testcases name when calling it from the
  commandline (you have to use the new name).

### Fixed
- `boot_to_shell` is no longer a public method of `BoardLinux` machines.


## [0.6.6] - 2019-01-18
### Added
- Graphviz `dot` diagram generator
- New and improved documentation!
- `LinuxMachine.fsroot`: A little convenience helper: You can now write
  `mach.fsroot / "proc/version"` instead of `linux.Path(mach, "/proc/version")`

### Changed
- tbot no longer automatically creates a log file.  If you want
  the previous behavior, use `--log-auto`.  `--log=<file>` will
  still behave as before.
- `generators/generate_htmllog.py` -> `generators/htmllog.py`
- `generators/debug_messages.py` -> `generators/messages.py`
- `UBootMachine.env()` now also accepts `board.Special`s.

### Fixed
- Duplication warning when star-importing another testcase-file.


## [0.6.5] - 2018-12-20
### Added
- `Machine.lh`: You can access the lab-host from every machine now.  The idea
  behind this is to allow access to lab-specific configuration in a much
  easier way.
- `mach.env()` can now be used to set environment variables as well:
  `env("name", "value")`
- `-p` for setting testcase parameters.  Provided values are parsed
  using `eval`, so be careful ... Example:

  ```bash
  $ tbot -p int_param=42 -p boolean=True -p string=\'str\'
  ```

### Changed
- You can now use `--log=` to suppress the creation of a log file.

### Fixed
- `selftest_path_stat` assuming the existence of `/dev/sda`, which makes
  it fail on systems without this block device.
- tbot will now only color its output if appropriate.
  It honors [CLICOLOR](https://bixense.com/clicolors/).


## [0.6.4] - 2018-12-05
### Added
- `-C` parameter to allow setting a different working directory
- `${TBOTPATH}` environment variable to provide additional testcase
  directories; `TBOTPATH` is a `:` separated list of directorie
- `auth.NoneAuthenticator`: Authenticator without key nor password, useful
  if ssh can figure authentication out by itself (eg with ssh-agent)
- `GitRepository.apply`: Apply patches without committing the changes

### Changed
- `linux.shell`: Shells now have a `shell.command`, which allows specifying
  a command to run the shell.  For example, bash is run using `bash --norc`
  now.

### Fixed
- timeout in `read_until_prompt` sometimes being negative
- log missing bootlog for U-Boot if no autoboot is configured
- tbot ignored ssh host aliases (ref #8)


## [0.6.3] - 2018-11-28
### Added
- `tbot.log.warning`: Print a warning message
- If tbot fails to load a testcase source, it will now show the
  traceback that caused the failure

### Changed
- Show any and all output that is received on the channel with `-vvv`
- `BoardLinuxMachine` now allows the login and password prompts to
  be clobbered
- `BoardLinuxMachine` login now waits for the shell to respond

### Removed
- `login_wait` config parameter from `BoardLinuxMachine`.  This "hack"
  is superseded by the more robust login implementation now.

### Fixed
- `importlib.util` needs to be manually imported on some python versions


## [0.6.2] - 2018-11-22
### Added
- `Machine.env`: Easily get the value of an environment variable
- Allow specifying a command when spawning a subshell.
- `ub.bootlog` and `lnx.bootlog` to allow accessing the bootlog (ref #5)
- Add `SSHMachine.ssh_config`: List of additional ssh config options


## [0.6.1] - 2018-11-16
### Added
- Proper buildhost support + U-Boot build testcase
- `GitRepository` now fetches latest changes from remote by default
- `LinuxMachine.subshell`: Spawn subshell to isolate context changes

### Changed
- Allow setting `autoboot_prompt` to `None`, if the board automatically drops
  into a U-Boot shell.
- Testcase directories are now traversed recurively
- `SSHLabHost` now attempts to use values from `~/.ssh/config` if available.
- `SSHMachine`: Use labhost's username by default


## [0.6.0] - 2018-11-08
Version 0.6.0 is finally here!  It is a complete rewrite so none of the old
stuff is relevant any more.  The changelog below is not everything that was
changed, but the changes since the last prerelease (`0.6.0-pre08`).

### Added
- `mach.test()` to just check the return code of a command
- `linux.F`, `board.F`: Formatter with TBot support
- `max` parameter for `Channel.recv()`
- `recv_n` method for `Channel` to read exactly N bytes
- `ignore_hostkey` in `SSHLabHost`
- `console_check` hook to prevent racey board connections
  from multiple developers
- `LinuxWithUBootMachine.do_boot` for a more flexible
  `boot_commands` definition

### Changed
- Improved testrun end handling
- Made `SSHMachine` more userfriendly; now shows ssh errors in log
- Made `shell` mandatory for `BoardLinux` machines

### Fixed
- `shell.copy` sometimes not respecting `ignore_hostkey` flag
- `shell.copy` relying on an ugly hack that breaks on some python versions
- `Verbosity` being in the wrong format in log events


## [0.6.0-pre08] - 2018-10-29
### Added
- Selftest that fails intentionally

### Changed
- *Internal*: `Board` no longer manages the boot-logevent as that breaks
  when no BoardMachine follows up

### Fixed
- HTMLLog generater producing bad HTML because of some log issues


## [0.6.0-pre07] - 2018-10-25
### Added
- Password support in `shell.copy`
- Recipes in documentation
- `Board.cleanup`, `Channel.register_cleanup`, ability to register a hook
  for cleaning a channel.  Might help if some lockfiles are kept when TBot
  just kills a connection.
- Support for copying from `LocalLabHost()` to `SSHLabHost()` and the other
  way around.
- `GitRepository.symbolic_head` to get current branch name

### Changed
- `GitRepository.bisect` now ensures that the good revision is actually good
  and the current revision is actually bad.

### Fixed
- Fix failures not leading to error return code
- Better error message if a board/lab was not found
- Stdout showing password prompt late
- Remove some escape sequences from log output to keep it tidy


## [0.6.0-pre06] - 2018-10-11
### Added
- Reimplemented Logging. The following generators have been updated:
    * `htmllog`
    * `junit`
- Support for password authentication on SSH machines.  **I strongly
  reccomend not using this!**

### Changed
- Updated documentation

### Fixed
- Fixed pre-commit selftest hook creating log files

### Removed
- Unnecessary files from pre 0.6 versions


## [0.6.0-pre05] - 2018-09-26
### Added
- `verbosity` parameter for `log.message`
- `ignore_hostkey` flag for `SSHMachine`s

### Changed
- More robust completions

### Fixed
- Program name in help and version message was wrong
- Better error messages when a testcase file can't be loaded
- Selftests failing because sshd host key changes
- `GitRepository` failing to reset in `__init__`


## [0.6.0-pre04] - 2018-09-19
### Added
- `GitRepository.head`: Get the current position of `HEAD`
- `GitRepository.bisect`: Bisect the git repo to find the commit
  which introduced a bug.
- Show durations of testcase runs.

### Changed
- Moved package metadata into `__about__.py`
- Always show long version in documentation
- `shell.copy` can now copy from and to SSHMachines.


## [0.6.0-pre] - 2018-08-28
Version **0.6.0** is basically a complete rewrite of TBot.  A rough summary of changes:
- Be as *pythonic* as possible, the old version had a big issue of non pythonic patterns
  making things that should be easy difficult.
- More static guarantees. New TBot can guarantee even more when checking your testcases with
  a static typechecker.  A big new feature in that regard is static guarantee of never using
  a path with a wrong machine!
- Cleaner and much smaller codebase.  Every piece of code is written as small and pythonic
  as possible which has made the codebase much more manageable.
- Speedups! New TBot can complete its selfchecks in under 1s. This is possible because of a
  new channel API that no longer uses sleep unless absolutely necessary.
- Much more stable and predictable.  Even more care was taken in making TBot behave as predictable
  as possible and reducing side effects.


## [0.3.4] - 2018-08-09
### Added
- `TestcaseFailure` & `InvalidUsageException` exceptions

### Changed
- Better error message when testcase does not exist
- More explicit exceptions

### Fixed
- Fixed TBot ignoring failures while applying patches (#13)
- Fixed -d not being allowed between board and testcase (#6)


## [0.3.3] - 2018-07-20
### Added
- `uboot.shell.autboot-keys`: Custom key sequence for intercepting
  autoboot (#9)
- Warning if an invalid testcase file is in the path (TBot no longer
  refuses to do anything, in this case)

### Changed
- Made scp config settings consistent with ssh settings (#10)

### Fixed
- Fixed TBot still clogging the user's history with commands (#7)
- Fixed testcase files not being able to import local submodules
- Fixed TBot errors being shown when attempting testcase completion (#11)


## [0.3.2] - 2018-07-12
### Added
- Comments in files generated by `tbot-mgr` to explain
  config options
- `-s`, `--show` command line option to get information about
  testcases
- `warning` and `error` log message functions

### Changed
- Removed `ssh_command` and added `ssh_flags` instead. This allows TBot
  to have more control over ssh

### Fixed
- Fixed TBot hanging when SSH asks for a password
- Fixed git bisecting


## [0.3.1] - 2018-06-22
### Added
- `tbot-mgr`: A script for managing TBot configs
- Testcases for building Linux
- `interactive_build_uboot` and `interactive_build_linux`
- Selftests are now run as a pre-commit hook
- A dummy lab and board for running selftests
  that are as generic as possible
- ``linux.revision`` and ``uboot.revision`` config keys

### Changed
- git testcases now have a `rev` parameter for checking out a specific
  revision

### Removed
- DENX specific configs

### Fixed
- A crash while checking the config


## [0.3.0] - 2018-06-15
### Added
- **Buildhosts:** This release adds the ability to build U-Boot/Linux
  on a separate machine. This will reduce load on your labhost if multiple
  people are using it
- You can now disable documentation for a testcase by passing
  `doc=False` to `tb.call`
- Added `-i/--interactive` commandline flag that will make TBot wait for user
  confirmation for each command it wants to execute. Use this if you are unsure
  whether your testcase will do anything harmful, because you can intervene if a
  critical command has ie. wrong parameters
- Added `retrieve_build_artifact` and `tbot_clean_builddir` tasks
- Added a new config key `build.local` that defines the buildhost that is the
  labhost itself
- More tests in `check_config`
- Better documentation

### Changed
- `uboot_checkout` now checks out U-Boot onto the default buildhost by default
- U-Boot is built on the buildhost by defalt, you need to use `retrieve_build_artifact`
  to copy binaries to the labhost
- Renamed `tbot_check_config` to `check_config`

### Fixed
- Removed an unnecessary shell check from U-Boot tests
- Fixed TBot "leaking" from a with statement


## [0.2.4] - 2018-05-28
### Added
- pre-commit hook config, run `pre-commit install` to use these
  hooks.
- Checks for malformed commands (eg. running `exit` or a command that
  contains a `\n`)

### Changed
- Use flake8 instead of pylint
- Reformat using black

### Fixed
- Fix the config not being properly installed and thus TBot not
  working outside a development environment
- Small visual errors that were created when moving to the
  new logger


## [0.2.3] - 2018-05-16
### Added
- New singleton logger `tbot.log`
- Warning when trying to generate documentation
  from unsuccessful TBot runs

### Changed
- The old logger was replaced by a new singleton implementation.
  This solves a few issues where the logger was not available
  when it should have been. Also, logging is a prime example for
  where to use a singleton. This will ensure that stdout is only
  used in one place and things don't get messy ...

### Removed
- Old `tbot.logger` module and it's `LogEvent`'s
- `TBot.log`

### Fixed
- U-Boot bootlog was not shown in very-verbose logging
- Documentation links not working properly
- The interactive shells were not properly handling the
  receival of multiple bytes at once, this is fixed now
- Path expansion in completions is now handled properly


## [0.2.2] - 2018-05-15
### Added
- **Commandline testcase parameters**: You can now pass parameters
  to testcases from the commandline using the `-p` or `--param`
  commandline parameter
- Completions for logfile
- More config documentation
- `shell_utils.command_and_retval`: Run a command on a channel
  and get it's return code

### Removed
- `@cmdline` decorator. All testcases are now callable from
  the commandline, for some you will need to use the new `-p`
  option to work properly

### Fixed
- Completions for `-c` were not always properly handled
  (`=` messed with argument splitting)


## [0.2.1] - 2018-05-14
### Changed
- Disable writing to history when setting up a channel
- Implement cleanup in interactive testcases so user code can continue
  after finishing an interactive session

### Fixed
- Fix KeyErrors not displaying the full path to the failing key


## [0.2.0] - 2018-05-04
### Changed
- Use custom bash completions instead of argcomplete
- Make the HTMLLog generator use a template. Eases development
  and reduces clutter in the source file. Also, the html logs
  no longer depend on the existence of the css file
- Implement better quiet handling. Adjust the verbosity
  levels of some log messages to ensure they are displayed
  when they should be

### Fixed
- Fix testcase EXPORTS. Exports are now in a separate file
  that is loaded before everything else. This should fix
  some testcases not working because exports they depend on
  were loaded later
- Fix `call_then` not returning the function itself
