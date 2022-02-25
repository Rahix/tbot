# Changelog

## [Unreleased]
### Added
- Added the `linux.Path.resolve()` method to turn relative paths absolute and
  to resolve all symlinked components of a path.  This is essentially
  `realpath(1)`.

### Fixed
- Fixed some problems with some busybox versions when using `Path.write_text()`
  for device property files in `/sys`.
- Fixed `linux.Workdir` sometimes returning a different workdir (when same "key" is
  used for multiple workdirs on the same host).


## [0.9.5] - 2022-02-14
### Added
- Added a new, reworked integration for U-Boot's test/py testsuite as
  [`tbot_contrib.uboot.testpy`].  Consider using this one in preference of the
  old `tbot.tc.uboot.testpy`.
- Added a `.board` property to all machines which were instantiated from a
  "board" (like a `BoardLinux`, for example).  This property points back to
  this original board machine.  See issue [#65] for a usecase of this.

### Removed
- Soft-removed the old selftest suite (which was called with `tbot selftest`)
  in favor of the new pytest based one.  Please selftest tbot with the
  following command instead:
  ```bash
  cd /path/to/tbot-sources
  python3 -m pytest selftest/
  ```

### Fixed
- Fixed a bug when using death-strings on a machine and then calling
  `LinuxShell.run()`.  This fixes spurious messages about the command having
  ended prematurely when it really hasn't.
- Fixed `Path.write_bytes()` and `Path.write_text()` raising an exception of the
  wrong type when an error occurs. This could sometimes even lead to improper
  behavior of follow-up commands.
- Fixed the `GDBShell` for versions of `gdb` which ask about enabling
  `debuginfod`.

[#65]: https://github.com/Rahix/tbot/issues/65
[`tbot_contrib.uboot.testpy`]: https://tbot.tools/contrib/uboot.html#tbot_contrib.uboot.testpy


## [0.9.4] - 2021-12-24
### Fixed
- Fix machine locking (`tbot_contrib.locking`) not quite working when
  `reset_on_error_by_default` is active in the tbot context.
- Fix `reset_on_error` raising odd exceptions when nested requests of the same
  machine are done.
- Fixed tbot not running with Python 3.10.
- Fixed `tbot_contrib.locking` locks not working properly on multi-user systems
  due to bad permissions.


## [0.9.3] - 2021-12-10
### Added
- Added the `NullConnector` for designing machine classes which do not have a
  channel.  This is useful, for example, when a board has no serial console.
- Added the `powercycle_delay` attribute to the `PowerControl` initializer.
  This can be used to specify a wait time between poweroff and subsequent
  poweron of a board.  Used to let the poweroff settle to have the board really
  off before turning it back on.
- Added an option to slow down transmission of a `Channel` for serial consoles
  which cannot process incoming data fast enough.  See [`Channel.slow_send_delay`]
  for details.
- Added a `Context.teardown_if_alive()` method to ensure no instance of a
  certain role is active.  This can be useful, for example, when a `BoardLinux`
  instance is alive but you need to enter U-Boot.  Normally this would fail,
  because the `BoardLinux` instance is keeping the `Board` instance for itself.
  With teardown_if_alive() you can first tear down this `BoardLinux` instance
  and then request the `BoardUBoot` instance as usual.

### Changed
- When a pytest testcase is skipped, `tbot.Context`'s `reset_on_error` flag no
  longer triggers a board reset.  This means skipping testcases is now just as
  fast as not executing them where it previosuly would trigger a reset of all
  machines.

### Fixed
- Fixed Linux machines not connecting when a very long `PS1` is used on the
  remote side.
- Fixed an exception during context teardown when `keep_alive` mode is enabled.
- Fixed `find_ip_address()` not working with the BusyBox version of the `ip`
  utility.

[`Channel.slow_send_delay`]: https://tbot.tools/modules/machine_channel.html#tbot.machine.channel.Channel.slow_send_delay


## [0.9.2] - 2021-09-13
### Added
- Added a new `strip_ansi_escapes()` utility in `tbot_contrib.utils` which can
  be used to remove e.g. color escape codes from command output.
- Added a `hashcmp()` utility in `tbot_contrib.utils` to compare the hashsum of
  two files (which may be located on different machines).
- Added the `py.typed` marker for type-checkers (see [PEP 561]).

### Fixed
- Fixed the order of instance teardown in `keep_alive` contexts.  This fixes any
  kinds of problems due to wrong teardown order of dependent machines (e.g.
  lab-host torn down before a board machine).
- Fixed selftests failing due to deprecation of `ssh-rsa` algorithm.
- Fixed `find_ip_address()` not working when a local address is passed as the
  `route_target`.

[PEP 561]: https://www.python.org/dev/peps/pep-0561/


## [0.9.1] - 2021-06-23
### Added
- Added a mechanism for "locking" connections to certain machines.  This can be
  used, for example, to ensure exlusive access to a certain board.  See
  [`tbot_contrib.locking`][tbot-locking] for details.
- `Path.rmdir()` and `Path.unlink()`: Methods to conveniently delete an empty
  directory, a symlink, or a file from a host's filesystem.
- `Path.mkdir()`: Method to conveniently create a directory on the respective
  machine.
- `Path.at_host(host)`:  A method to safely convert a tbot-path into a plain
  string.  The `host` parameter is used to check that the `Path` is actually
  meant for the expected host.  Any uses of the (unofficial) `_local_str()`
  method should be replaced by `at_host()` as the former will be removed soon.
- New classes `AppendStdout`, `AppendStderr`, and `AppendBoth` in
  `machine.linux` allow to append command output to files in `exec()` and
  `exec0()` methods.
- Added a feature to the `Context` to allow reconfiguring a context temporarily
  (`Context.reconfigure()`).  This is useful to e.g. enable `keep_alive` mode
  for certain tests.

### Changed
- Warnings emitted due to problems when parsing the SSH config now include
  hints about the actual problem.
- `linux.Path` no longer inherits from `pathlib.PurePosixPath`.  This fixes
  a number of long standing oddities where certain methods would not function
  correctly.  All API from `PurePosixPath` has been reimplemented in
  `linux.Path` explictly, now with the proper behavior.

### Fixed
- Fixed the `PyserialConnector` not working properly with tbot contexts.
- Fixed `linux.Background` not properly redirecting stderr output.

[tbot-locking]: https://tbot.tools/contrib/locking.html


## [0.9.0] - 2021-03-03
### Added
- Added the **Context** API for much easier and more flexible machine
  management.  Please read the [Context API][context-api] documentation for an
  introduction and migration guide.  **Note**: For now the old `tbot.selectable`
  API still exists and will be compatible both ways with the new API.  It will,
  however, slowly be phased out in the future.
- Warning about incorrect build-host configuration when running `uboot_testpy`
  testcase.
- Added support for SSH connection multiplexing to `SSHConnector`.  You can
  enable it by adding `use_multiplexing = True` to your host config.
  Multiplexing can drastically speed up testcases which open many connections to
  the same host (see [`ControlMaster` in `sshd_config(5)`][ssh-multiplexing] for
  details).
- Added two more types of machine initializers:
  - [`PreConnectInitializer`][pre-connect-initializer]: Runs before the
    connection is established.
  - [`PostShellInitializer`][post-shell-initializer]: Runs after the shell is
    available (and thus can interact with it).

### Changed
- `LinuxShell.env()` can now be used to query `$!` (last background job PID) and
  `$$` (current shell PID) special environment  variables (using `m.env("!")`
  and `m.env("$")`).
- Added some more specific exception types and started using them where
  appropriate.  This effort is by far not over yet, though ...
- The `linux.Background` special token is now more safe to use as it prevents
  console clobbering as good as it can.  You can manually redirect command
  output to files using a new call syntax.  See [`Background`][linux-background]
  documentation for details.
- `paramiko` is now an optional dependency.  tbot works just fine without
  paramiko, but if it is installed, the `ParamikoConnector` becomes available.
- Switched to `pytest` for tbot's selftests.

### Fixed
- Call `olddefconfig` before attempting to build U-Boot.  This prevents kconfig
  from attempting to interactively query new config settings.
- Fixed a rare timing-dependent bash/ash initialization deadlock.
- Fixed `selftest_tc` failing if user has no git identity set up.
- Fixed documentation silently building without version information if
  `git describe` fails.
- Fixed tbot configuring an overly narrow terminal in some cases, leading to
  weird looking output (now the minimum is 80 chars wide).
- Fixed `Path.write_text()`/`Path.write_bytes()` hanging when an error occurs
  and the channel receives data very slowly.

[context-api]: https://tbot.tools/context.html
[ssh-multiplexing]: https://man.openbsd.org/ssh_config.5#ControlMaster
[linux-background]: https://tbot.tools/modules/machine_linux.html#tbot.machine.linux.Background
[pre-connect-initializer]: https://tbot.tools/modules/machine.html#tbot.machine.PreConnectInitializer
[post-shell-initializer]: https://tbot.tools/modules/machine.html#tbot.machine.PostShellInitializer


## [0.8.3] - 2020-09-22
### Added
- Added `ensure_sd_unit()` testcase/util-function which starts systemd
  services if not yet running.
- `tbot.error` module as a central place for defining all exception types.
- Added a `PyserialConnector` to connect to a serial port using
  [PySerial][pyserial].
- super-verbose mode (`-vvv`) now prefixes each output line with a channel
  identifier to help separate what data came from which channel.
- Added a `Channel.read_until_timeout()` method for reading all data until
  a timeout is reached (or an Exception is thrown).
- Added `find_ip_address()` testcase/util-function to discover the IP
  address of a machine.
- One can now pass a custom line-ending to `Channel.readline()` incase the
  remote does not behave properly and send `\r\n` for every line.
- Added a `Channel.add_death_string()` method which is like
  `.with_death_string()` but not a context-manager.  The death string is
  added for the entire lifetime of the channel with this new method.

### Changed
- tbot now prints all passed flags on start (and thus also stores this
  info in the log-file).
- The `\e[K` is passed through to make output from programs like
  ninja-build prettier.

### Fixed
- Fixed an issue where the path returned by `mach.workdir` would be
  associated with a wrong host machine.
- Fixed bash completions for `@args` not properly dealing with
  directories.
- Fixed `login_delay` for board-linux not behaving as documented and in
  some circumstances leading to a login without waiting.

[pyserial]: https://pyserial.readthedocs.io/en/latest/pyserial.html


## [0.8.2] - 2020-04-08
_Update_: Development now happens on the `master` branch instead of `development`.

### Added
- Added `LinuxShell.run()` to run a command and interact with its stdio:
  ```python
  with lh.run("gdb") as gdb:
      gdb.read_until_prompt("(gdb) ")
      gdb.sendline("target remote 127.0.0.1:3333")
      gdb.read_until_prompt("(gdb) ")
      gdb.sendline("load")
      gdb.read_until_prompt("(gdb) ")
      gdb.sendline("quit")
      gdb.terminate0()
  ```
- `Path.write_text()`, `Path.read_text()`, `Path.write_bytes()`, and
  `Path.read_bytes()`: Methods to easily manipulate remote files.
- Added integration for U-Boot's test/py test-framework.  See the
  ``uboot_testpy`` testcase fore more.
- A connector for connection to a [conserver](https://www.conserver.com/)
  based serial console: `tbot_contrib.connector.conserver`
- Testcases for timing the duration of an operation (`tbot_contrib.timing`).
- A testcase to deploy an `swu`-file to
  [SWUpdate](https://github.com/sbabic/swupdate) (`tbot_contrib.swupdate`).
- Machines now implement `==` and `hash()`.  A machine which was cloned
  from another machine has the same hash, i.e. they can be treated as equal.
- Added a U-Boot smoke-test: `tbot.tc.uboot.smoke_test()` or `uboot_smoke_test`
- Added a `DistroToolchain` class to easily allow using pre-installed
  toolchains with tbot.
- Added a Workdir which lives in ``$XDG_DATA_HOME`` and one living in
  ``$XDG_RUNTIME_DIR`` (``Workdir.xdg_home()`` and ``Workdir.xdg_runtime()``).
- You can now specify the U-Boot revision to checkout:
  ``tbot uboot_checkout -prev=\"v2020.01\"``
- A ``boot_timeout`` parameter was added to U-Boot machines to limit the maximum
  time, U-Boot is allowed to take during boot.
- Testcases for interacting with GPIOs (`tbot_contrib.gpio`).
- ``tbot.Re``: A convenience wrapper around ``re.compile``.  Whereever
  regex-patterns are needed (e.g. in channel-interaction), you can now use
  `tbot.Re` instead of `re.compile("...".encode())`.
- A `Channel.readline()` and a `Channel.expect()` method to mimic pexpect.

### Changed
- The default workdir for Linux shells is no longer `/tmp/tbot-wd`.  It is
  now `$XDG_DATA_HOME/tbot` (usually `~/.local/share/tbot`).
- `UBootBuilder` now points to the new U-Boot upstream
  (<https://gitlab.denx.de/u-boot/u-boot.git>) by default.
- Fixed `linux.Bash`'s `.env()` implementation unnecessarily querying the
  variable after setting it.
- ``selftest`` now uses a dedicated machine class which does not clobber
  the default workdir and instead stores data in a temporary directory.

### Fixed
- Fixed tbot sometimes not displaying a message before entering
  interactive mode, thus leaving the user clueless what escape-sequence to
  use to exit.
- Fixed `linux.Bash`, `linux.Ash`, and `board.UBootShell` allowing some
  bad characters in command invocations which would mess up the shell's
  state.
- Fixed `tbot.flags` only being set _after_ loading the testcases which
  could lead to weird inconsistency errors.
- Fixed ``Channel.sendcontrol()`` not actually allowing all C0 control
  characters.


## [0.8.1] - 2020-03-06
### Added
- Added `LinuxShell.glob()` method for easily using shell globs.
- Added parameters to `LinuxShell.subshell()` which can be used to spawn
  custom subshells.
- Added `linux.RedirBoth` to redirect both stdout and stderr to the same
  file.
- Added `UBootShell.ram_base` property to learn the RAM base address in
  testcases.
- Added a write blacklist to channels.  This feature can be used to
  disallow tests sending certain control characters.
- Added a `do_build()` step to `UBootBuilder` which can be used to
  customize the command used for building U-Boot.
- Empty `tbot_contrib` module for the future :)

### Changed
- Made `SSHConnector` based machine cloneable (if the underlying host is
  cloneable).
- Made `tbot.testcase` also work as a context-manager.  This can be used
  to define 'sub-tests' in a function.  Example:

  ```python
  with tbot.testcase("my_sub_testcase"):
      ...
  ```

### Fixed
- Fixed U-Boot and board-Linux not saving the bootlog to the log-event.
- Fixed tbot happily printing special characters as part of a command which was
  sent (in the log).
- Fixed selftests failing in some rare circumstances because a subprocess
  is not properly terminated or when bash is slow.
- Removed use of the deprecated `time.clock()` function.
- Properly check stdout encoding.
- Fixed `read_iter` sometimes passing negative timeout values to the
  underlying channel IO.
- Fixed tbot hanging on zero-byte `Channel.send()` call.
- Fixed `lnx.env()` behaving incorrectly when an environment variable has
  a value which looks like an `echo`-option.
- Fixed a bug caused by passing `"\n^"` as a parameter (bash interprets this as
  a kind of history expansion).
- Fixed `UBootShell` not properly escaping `\` and `'`.
- Fixed `ub.env()` failing on environment variables with weird values.


## [0.8.0] - 2019-11-20
The machine interface was completely overhauled.  Please read the [migration
guide](https://tbot.tools/migration.html) for more info.

### Added
- `@tbot.with_lab`, `@tbot.with_uboot`, and `@tbot.with_linux` decorators to
  make writing testcase much simpler
- `linux.RedirStdout(f)` & `linux.RedirStderr(f)`: Redirect stdout and stderr symbols
- `Machine.init()` hook to call custom code after the machine was initialized.
  This can be used, for example, to init network manually in U-Boot.
- `tc.shell.check_for_tool()` testcase
- `tbot.skip()`: Skip a testcase
- `Machine.clone()`: Attempt creating a copy of a machine.  The two copies
  allow parallel interaction with the same host.

### Changed
- `linux.BuildMachine` is now a mixin called `linux.Builder`
- `linux.LabHost` is now a mixin called `linux.Lab`
- `linux.LinuxMachine` should be replaced by `linux.LinuxShell`
- `LabHost.new_channel()` was removed in favor of `LinuxShell.open_channel()`.
  `open_channel()` consumes the machine it is called on which means the
  equivalent to `new_channel()` now is:

  ```python
  with mach.clone() as cl:
      chan = cl.open_channel("telnet", "192.0.2.1")
  ```

### Removed
- `exec0(stdout=f)`: Redirection should be done using `RedirStdout`.
- `linux.Env(var)`: Environment-Variable substitution is hard to control.  It
  is much easier to just use `mach.env(var)`.

### Fixed
- `Path.__fspath__()` erroneously returning a result, even though the contract
  that is assumed with this method cannot be upheld by tbot.


## [0.7.1] - 2019-03-14
### Added
- `tbot.acquire_local()`: Quick access to a localhost machine
- `LinuxMachine.home`: Path to the current user's home
- `LocalLabHost.tbotdir`: tbot's current working directory on the localhost (either
  from where you ran `tbot` or the path given with `-C`)
- `tbot.tc.kconfig`:  Testcases for modifying a kernel config file
- `login_delay`: Time to wait before logging in on the board.  This should
  allow working with boards that clobber the console a lot during boot.

### Changed
- Unknown parameters are now ignored if running multiple testcases so
  you can specify parameters that are just relevant to a single one.
- `SSHMachine`s now use `NoneAuthenticator` by default.

### Fixed
- `selftest`s sometimes failing if dropbear does not start fast enough
- `SSHMachine`s using the local user's home dir instead of the one on the
  lab-host.
- Local channels now correctly end the session which fixes weird bugs like
  picocom not being able to reaquire the shell.


## [0.7.0] - 2019-02-08
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

### Changed
- The U-Boot build testcase has been completely rewritten.  You will need to
  adapt you board config to work with the new version:

  * The build-info no longer exists, instead you define a `UBootBuilder`.  Take
    a look at the docs to see available options.
  * The build attribute of your U-Boot machine must now be an **instance** of
    your `UBootBuilder`, **not** the class itself.

  Example of the new config:

  ```python
  from tbot.machine import board
  from tbot.tc import uboot

  class MyUBootBuilder(uboot.UBootBuilder):
      name = "my-builder"
      defconfig = "my_defconfig"
      toolchain = "generic-armv7a-hf"

  class MyUBootMachine(board.UBootMachine):
      ...
      build = MyUBootBuilder()
  ```

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


## 0.2.0 - 2018-05-04
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

[Unreleased]: https://github.com/Rahix/tbot/compare/v0.9.5...master
[0.9.5]: https://github.com/Rahix/tbot/compare/v0.9.4...v0.9.5
[0.9.4]: https://github.com/Rahix/tbot/compare/v0.9.3...v0.9.4
[0.9.3]: https://github.com/Rahix/tbot/compare/v0.9.2...v0.9.3
[0.9.2]: https://github.com/Rahix/tbot/compare/v0.9.1...v0.9.2
[0.9.1]: https://github.com/Rahix/tbot/compare/v0.9.0...v0.9.1
[0.9.0]: https://github.com/Rahix/tbot/compare/v0.8.3...v0.9.0
[0.8.3]: https://github.com/Rahix/tbot/compare/v0.8.2...v0.8.3
[0.8.2]: https://github.com/Rahix/tbot/compare/v0.8.1...v0.8.2
[0.8.1]: https://github.com/Rahix/tbot/compare/v0.8.0...v0.8.1
[0.8.0]: https://github.com/Rahix/tbot/compare/v0.7.1...v0.8.0
[0.7.1]: https://github.com/Rahix/tbot/compare/v0.7.0...v0.7.1
[0.7.0]: https://github.com/Rahix/tbot/compare/v0.6.6...v0.7.0
[0.6.6]: https://github.com/Rahix/tbot/compare/v0.6.5...v0.6.6
[0.6.5]: https://github.com/Rahix/tbot/compare/v0.6.4...v0.6.5
[0.6.4]: https://github.com/Rahix/tbot/compare/v0.6.3...v0.6.4
[0.6.3]: https://github.com/Rahix/tbot/compare/v0.6.2...v0.6.3
[0.6.2]: https://github.com/Rahix/tbot/compare/v0.6.1...v0.6.2
[0.6.1]: https://github.com/Rahix/tbot/compare/v0.6.0...v0.6.1
[0.6.0]: https://github.com/Rahix/tbot/compare/v0.6.0-pre08...v0.6.0
[0.6.0-pre08]: https://github.com/Rahix/tbot/compare/v0.6.0-pre07...v0.6.0-pre08
[0.6.0-pre07]: https://github.com/Rahix/tbot/compare/v0.6.0-pre06...v0.6.0-pre07
[0.6.0-pre06]: https://github.com/Rahix/tbot/compare/v0.6.0-pre05...v0.6.0-pre06
[0.6.0-pre05]: https://github.com/Rahix/tbot/compare/v0.6.0-pre04...v0.6.0-pre05
[0.6.0-pre04]: https://github.com/Rahix/tbot/compare/v0.6.0-pre...v0.6.0-pre04
[0.6.0-pre]: https://github.com/Rahix/tbot/compare/v0.3.4...v0.6.0-pre
[0.3.4]: https://github.com/Rahix/tbot/compare/v0.3.3...v0.3.4
[0.3.3]: https://github.com/Rahix/tbot/compare/v0.3.2...v0.3.3
[0.3.2]: https://github.com/Rahix/tbot/compare/v0.3.1...v0.3.2
[0.3.1]: https://github.com/Rahix/tbot/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/Rahix/tbot/compare/v0.2.4...v0.3.0
[0.2.4]: https://github.com/Rahix/tbot/compare/v0.2.3...v0.2.4
[0.2.3]: https://github.com/Rahix/tbot/compare/v0.2.2...v0.2.3
[0.2.2]: https://github.com/Rahix/tbot/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/Rahix/tbot/compare/v0.2.0...v0.2.1
