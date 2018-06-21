# Changelog

## [Unreleased]
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
