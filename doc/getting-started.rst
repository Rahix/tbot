.. highlight:: guess
   :linenothreshold: 3

Getting Started
===============

First Steps
-----------
TBot works out of the box.  You can run it's selftests like this::

    ~$ tbot selftest

(If this does not work, please contact the developers.  This should not be the case)

Now, let's create some example testcase.  Start by creating a file named ``tc.py`` in
your current directory.  Later you will see that you can also name it differently or
have multiple files, but for now, this is the easiest way.  Add the following content::

    import tbot

    @tbot.testcase
    def my_awesome_testcase() -> None:
        with tbot.acquire_lab() as lh:
            name = lh.exec0("uname", "-n").strip()
            tbot.log.message(f"Hello {name}!")

If you did everything correctly, running

::

    ~$ tbot my_awesome_testcase


.. highlight:: python
   :linenothreshold: 3

should greet you host.  Let's disect the code from above::

    @tbot.testcase
    def my_awesome_testcase() -> None:
        ...

This is just a normal python function for our testcase.  The :func:`tbot.testcase`
decorator tells TBot that it should be treated as a testcase.  In practice this
means that TBot will allow calling it from the commandline and will hook into
the call so it can gather log data about it.

::

    with tbot.acquire_lab() as lh:
        ...

To understand this line, we first need to get to know one of the core concepts of TBot:
**Machines** (:class:`~tbot.machine.Machine`).  Every host TBot interacts with is called a machine.
That includes the labhost, which we use here, a buildhost where your code might be compiled,
the board you are testing, or any other host you want TBot to connect to.  There are different kinds
of machines.  Our labhost is special, because it is the base from where connections to other host
are made.

Machines should always be used inside a ``with`` statement to ensure proper cleanup in any
case.  This is especially important with boardmachines, because if this is not done, the board
might not be turned off after the tests.

The line you see here requests a new labhost object from TBot so we can interact with it.
As you will see later, this is not quite the way you would do this normally, but for this simple
example it is good enough.

::

    name = lh.exec0("uname", "-n").strip()

Now that we have the ability to interact with the labhost, let's do so: We call
``uname -n`` to greet the users machine.  Note, that each argument is passed separately to
:meth:`~tbot.machine.linux.LinuxMachine.exec0`.  The reason for this is that it ensures everything
will be properly escaped and there are no accidental mistakes.  For special characters there is
a different notation as you will see later.

The :meth:`~str.strip` is needed, because the command output contains the trailing newline, which we don't
want in this case.

::

    tbot.log.message(f"Hello {name}!")

:func:`tbot.log.message` is basically TBot's equivalent of :func:`print`.  The most important difference is, that it does not
only print it to the terminal, but also store it in the logfile.

.. note::
    TBot has different **Verbosity** levels:

    * ``QUIET``: Only show testcases that are called
    * ``INFO``: Show info messages, such as those created by :func:`tbot.log.message`
    * ``COMMAND``: Show all commands that are called on the various machine
    * ``STDOUT``: Also show commands outputs
    * ``CHANNEL``: Show everything received on all channels, useful for debugging

    The default is ``INFO``. You can increase the Verbosity using ``-v`` and decrease it using ``-q``.

Writing Testcases
-----------------
As mentioned above, testcases calling :func:`tbot.acquire_lab` is not the best way to do it.  Why?  Well, imagine,
each testcase that is called would create a new ssh connection to your labhost.  This would be really
inefficient.  The easiest solution is to require the lab as a parameter like this::

    import tbot
    from tbot.machine import linux

    @tbot.testcase
    def my_testcase(lab: linux.LabHost) -> None:
        ...

This has the big disadvantage that a testcase like this can't be called from TBot's commandline, because
where would it get that parameter from?

The solution is a hybrid and looks like the following::

    import typing
    import tbot
    from tbot.machine import linux

    @tbot.testcase
    def my_testcase(
        lab: typing.Optional[linux.LabHost] = None,
    ) -> None:
        with lab or tbot.acquire_lab() as lh:
            name = lh.exec0("uname", "-n").strip()
            tbot.log.message(f"Hello {name}!")

This is one of my 'recipes'.  These are code snippets that you will reuse all the time while using
TBot.  There are a lot more, for different tasks.  Take a look at the :ref:`recipes:Recipes` page.

.. note::
    In this documentation and in the TBot sources, type annotations are used everywhere.  This allows
    the use of a static type-checker such as ``mypy``, which makes finding bugs before you even run
    the code a lot easier.  Of course, this is optional, the following code would work just as well::


        import tbot

        @tbot.testcase
        def my_testcase(lab = None) -> None:
            with lab or tbot.acquire_lab() as lh:
                name = lh.exec0("uname", "-n")
                tbot.log.message(f"Hello {name}!")

Calling other testcases is just as easy as calling a python function.  From your perspective, a testcase
*is* just a python function.  If you want to call testcases from other files, import them like you would
with a python module.

TBot contains a library of testcases for common tasks that you can make use of.  Take a look at :mod:`tbot.tc`.


Machine Interaction
-------------------

Linux
^^^^^
All :class:`~tbot.machine.linux.LinuxMachine` implement two methods for executing commands:
:meth:`~tbot.machine.linux.LinuxMachine.exec` and :meth:`~tbot.machine.linux.LinuxMachine.exec0`.
:meth:`~tbot.machine.linux.LinuxMachine.exec0` is just a wrapper around
:meth:`~tbot.machine.linux.LinuxMachine.exec` that ensures the return code of the command is ``0``.
Both take the command as one argument per commandline parameter.  For example::

    output = m.exec0("uname", "-n")
    output = m.exec0("dmesg")
    output = m.exec0("echo", "$!#?")

TBot will ensure that arguments are properly escaped, so you can pass in anything without worrying.
This poses a problem, when you need special syntaxes.  For example when you try to use shell expansion
of environment variables.  To do this, use the following::

    from tbot.machine import linux

    user = m.exec0("echo", linux.Env("USER"))

This is not the only special parameter you can use:

* :func:`~tbot.machine.linux.Env`: Environment variable expansion
* :data:`~tbot.machine.linux.Pipe`: A ``|`` for piping command output to another command
* :data:`~tbot.machine.linux.Then`: A ``;`` for running multiple commands
* :data:`~tbot.machine.linux.Background`: A ``&`` for running a command in the background
* :data:`~tbot.machine.linux.AndThen`: A ``&&`` for chaining commands
* :data:`~tbot.machine.linux.OrElse`: A ``||`` for error handling
* :func:`~tbot.machine.linux.Raw`: Raw string if TBot isn't expressive enough for your usecase.
  Use this only when no other option works.


Another thing TBot handles specially is paths.  A :class:`~tbot.machine.linux.Path` can be
created like this::

    from tbot.machine import linux

    p = linux.Path(machine, "/foo/bar")

``p`` is now a :class:`~tbot.machine.linux.Path`.  TBot's paths are based on
python's :mod:`pathlib` so you can use all the usual methods / operators::

    file_in_p = p / "dirname" / "file.txt"
    if not p.exists():
        ...
    if not p.is_dir():
        raise RuntimeError(f"{p} must be a directory!")

TBot's paths have a very nice property: They are bound to the host they were created with.  This means
that you cannot accidentally use a path on a wrong machine::

    m = tbot.acquire_lab()
    lnx = tbot.acquire_linux(...)

    p = linux.Path(m, "/path/to/somewhere/file.txt")

    # This will raise an Exception and will be catched by a static typechecker like mypy:
    content = lnx.exec0("cat", p)

Board
^^^^^
Interacting with the board is similar to interacting with a host like the labhost.  The only difference
is that this time, we need to first initialize the board::

    with tbot.acquire_board(lh) as b:
        with tbot.acquire_uboot(b) as ub:
            ub.exec0("version")

            # Now boot into Linux
            with tbot.acquire_linux(ub) as lnx:
                lnx.exec0("uname", "-a")


    # You can also boot directly into Linux:
    # (Some boards might not even support intercepting
    # U-Boot first)
    with tbot.acquire_board(lh) as b:
        with tbot.acquire_linux(b) as lnx:
            lnx.exec0("uname", "-a")

.. note::
    A pattern similar to the one above can be used to write testcases that can either be used from
    the commandline or supplied with a board-machine::

        import contextlib
        import typing
        import tbot
        from tbot.machine import board


        @tbot.testcase
        def my_testcase(
            lab: typing.Optional[tbot.selectable.LabHost] = None,
            uboot: typing.Optional[board.UBootMachine] = None,
        ) -> None:
            with contextlib.ExitStack() as cx:
                lh = cx.enter_context(lab or tbot.acquire_lab())
                if uboot is not None:
                    ub = uboot
                else:
                    b = cx.enter_context(tbot.acquire_board(lh))
                    ub = cx.enter_context(tbot.acquire_uboot(b))

                ...


    Again, take a look at the :ref:`recipes:Testcase with U-Boot` section on the :ref:`recipes:Recipes`
    page.

Interactive
^^^^^^^^^^^
One convenience function of TBot is allowing the user to directly access most machines' shells.  There are
two ways to do so.

.. highlight:: guess
   :linenothreshold: 3

1. Calling one of the ``interactive_lab``, ``interactive_build``, ``interactive_board``, ``interactive_uboot``
   ``interactive_linux`` testcases.  This is the most straight forward.  It might look like this::

        ~$ tbot -l labs/mylab.py -b boards/myboard.py interactive_uboot

.. highlight:: python
   :linenothreshold: 3

2. Calling ``machine.interactive()`` in your testcase.  For example::

        with tbot.acquire_board(lh) as b:
            with tbot.acquire_linux(b) as lnx:
                lnx.exec0("echo", "Doing some setup work")

                # Might raise an Exception if TBot was not able to reaquire the shell after
                # the interactive session
                lnx.interactive()

                lnx.exec0("echo", "Continuing testcase after the user made some adjustments")
