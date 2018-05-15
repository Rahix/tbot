# Changelog

## [Unreleased]
### Added
- New singleton logger `tbot.log`

### Changes
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
### Changes
- Disable writing to history when setting up a channel
- Implement cleanup in interactive testcases so user code can continue
  after finishing an interactive session

### Fixes
- Fix KeyErrors not displaying the full path to the failing key


## [0.2.0] - 2018-05-04
### Changes
- Use custom bash completions instead of argcomplete
- Make the HTMLLog generator use a template. Eases development
  and reduces clutter in the source file. Also, the html logs
  no longer depend on the existence of the css file
- Implement better quiet handling. Adjust the verbosity
  levels of some log messages to ensure they are displayed
  when they should be

### Fixes
- Fix testcase EXPORTS. Exports are now in a separate file
  that is loaded before everything else. This should fix
  some testcases not working because exports they depend on
  were loaded later
- Fix `call_then` not returning the function itself
