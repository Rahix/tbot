.. _context:

Context
=======
The *context* is the new mechanism in tbot for managing machine instances.
Under the hood, the old configuration mechanism and the
:py:mod:`tbot.selectable` module are already using the context but using it
directly gives you even more power!

.. note::

   If you want to migrate from the "old" way of accessing the configured
   machines, please read the :ref:`context_migration` guide at the end of this
   page.  Though it is a good idea to first familiarize yourself with the new
   concepts.

The idea
--------
At the core, everything revolves around a context object:

 - Configuration registers machines with the context object (See
   :ref:`tbot_ctx_config`).
 - Testcases can then request instances of registered machines (See
   :ref:`tbot_ctx`).

Machines are registered for fulfilling certain :ref:`roles <tbot_role>`.  For
example the lab-config should register a machine for the
:py:class:`tbot.role.LabHost` role while the board-config registers machines for
e.g.  :py:class:`tbot.role.Board` and :py:class:`tbot.role.BoardLinux`.

When a testcase requests a machine, the instance that is created is *cached*.
That means when a later testcase requests the same machine (before the first one
released it again!), it will get access to the *same* instance.

.. _tbot_ctx:

The ``tbot.ctx`` object
-----------------------
tbot defines a global context as ``tbot.ctx``.  Testcases can directly interact
with this context to access machines.  See the :py:class:`tbot.Context` class
for the full API.  Essentially, there are two design patterns for testcases:

Single Machine
^^^^^^^^^^^^^^
.. code-block:: python

   @tbot.testcase
   def test_with_labhost():
       with tbot.ctx.request(tbot.role.LabHost) as lh:
           lh.exec0("uname", "-a")

Multiple Machines
^^^^^^^^^^^^^^^^^
This is analogous to pythons own :py:class:`contextlib.ExitStack` and useful
when you need multiple machines (= multiple context-managers) in one testcase:

.. code-block:: python

   @tbot.testcase
   def test_with_board_and_lab():
      with tbot.ctx() as cx:
         lh = cx.request(tbot.role.LabHost)
         lnx = cx.request(tbot.role.BoardLinux)

         lh.exec0("hostname")
         lnx.exec0("hostname")

Keeping tests flexible
^^^^^^^^^^^^^^^^^^^^^^
When writing reusable testcases, you should always prepare them for situations
where a caller would want to pass in custom machines instead of the ones
registered in the context.  The best way to do this is this:

.. code-block:: python

   @tbot.testcase
   def reusable_test_one_machine(m: Optional[LinuxShell] = None):
       with tbot.ctx() as cx:
           if m is None:
               m = cx.request(tbot.role.LabHost)

           ...

   @tbot.testcase
   def reusable_test_multiple(
       lab: Optional[LinuxShell] = None,
       ub: Optional[UBootShell] = None,
   ):
       with tbot.ctx() as cx:
           if lab is None:
               lab = cx.request(tbot.role.LabHost)
           if ub is None:
               ub = cx.request(tbot.role.BoardUBoot)

           ...

.. todo::

   Eventually, tbot might grow a new decorator for making contex usage even
   easier.  For now the above patterns are what should be used.

Complex Testcases (e.g. Powercycle)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Sometimes, testcases need to do more complex things with instances than to
simply interact with them.  A common example would be a powercycle of a DUT.
For such cases, the :py:meth:`Context.request() <tbot.Context.request>` method
provides some keyword arguments to allow fine-grained control over instance
requesting.

For the DUT powercycle example, a testcase might look like this:

.. code-block:: python

   @tbot.testcase
   def test_with_dut_reboot():
       with tbot.ctx.request(tbot.role.BoardLinux) as lnx:
           # Do some things before powercycle
           lnx.exec0("hwclock", "--systohc")

       with tbot.ctx.request(tbot.role.BoardLinux, reset=True) as lnx:
           # The DUT was powercycled before entering this context
           lnx.exec0("hwclock", "--hctosys")

.. _tbot_role:

Roles
-----
The :py:mod:`tbot.role` module pre-defines a number of roles that are commonly
needed in embedded automation and testing.  These roles are also what testcases
distributed alongside tbot use.  As an overview (details are in the
:py:mod:`tbot.role` module documentation):

 - :py:class:`tbot.role.LabHost`
 - :py:class:`tbot.role.BuildHost`
 - :py:class:`tbot.role.LocalHost`
 - :py:class:`tbot.role.Board`
 - :py:class:`tbot.role.BoardUBoot`
 - :py:class:`tbot.role.BoardLinux`

However, you can also define your own roles for more complex scenarios!  The
role should inherit :py:class:`tbot.role.Role` and any ABCs that a machine-class
implementing the role uses.  For example, a role for a Linux machine should
probably inherit :py:class:`tbot.machine.linux.LinuxShell`.  Or a role for
a U-Boot machine should inherit :py:class:`tbot.machine.board.UBootShell`.

.. _tbot_ctx_config:

Configuration
-------------
For :py:mod:`tbot.selectable`, machines were configured via globals in the lab-
and board-config named ``LAB``, ``BOARD``, ``UBOOT``, and ``LINUX``.  This still
works and will actually register the machines in :py:data:`tbot.ctx` under the
hood.

The new context-based configuration works slightly different:  lab- and
board-config scripts should define a global ``register_machines()`` function
that registers all machines from this config into the supplied context using
:py:meth:`tbot.Context.register`.  The method documentation explains the details
of registration but here are two examples:

Example lab-config
^^^^^^^^^^^^^^^^^^
.. code-block:: python

   class MyLab(...):
       ...

   class MyBuildHost(...):
       ...

   def register_machines(ctx: tbot.Context) -> None:
       ctx.register(MyLab, tbot.role.LabHost)
       # Optionally register a build-host as well
       ctx.register(MyBuildHost, tbot.role.BuildHost)

       # You could also register MyLab for both LabHost and BuildHost:
       ctx.register(MyLab, [tbot.role.LabHost, tbot.role.BuildHost])

Example board-config
^^^^^^^^^^^^^^^^^^^^
.. code-block:: python

   class MyBoard(...):
       ...

   class MyBoardLinux(...):
       ...

   def register_machines(ctx: tbot.Context) -> None:
       ctx.register(MyBoard, tbot.role.Board)
       ctx.register(MyBoardLinux, tbot.role.BoardLinux)

Controlling machine instanciation
---------------------------------
When a testcase calls :py:meth:`tbot.Context.request` to request a machine
instance, this instance needs to be created which is not trivial in all cases.
The context relies on the :py:meth:`Connector.from_context()
<tbot.machine.connector.Connector.from_context>` classmethod of the registered
machine-class for this.

Most connectors come with a reasonable default implementation of this method
which often just requests the prerequisite machines from the context and then
constructs the machine-class using them.  As an example, here is the
implementation of ``from_context()`` for
:py:class:`~tbot.machine.connector.ConsoleConnector`:

.. code-block:: python

    @classmethod
    @contextlib.contextmanager
    def from_context(cls, ctx: "tbot.Context"):
        with contextlib.ExitStack() as cx:
            # Will try to connect to console from lab-host, thus request
            # lab-host here:
            lh = cx.enter_context(ctx.request(tbot.role.LabHost))

            # Then instanciate the machine-class using `lh`:
            m = cx.enter_context(cls(lh))
            yield m

For more complex scenarios, lab- or board-config can of course overwrite this
method with custom behavior.  Please keep in mind the special semantics of
:py:meth:`Connector.from_context()
<tbot.machine.connector.Connector.from_context>` which are detailed in the
method documentation.

.. _context_migration:

Migrating to Context
--------------------
If you are interested in converting existing testcases and configuration to the
new "Context" API, this guide is for you.  For the most part the changes are
small and can be done incrementally as the new API is compatible with old code
& the other way around.

Migrating Testcases
^^^^^^^^^^^^^^^^^^^
The following functions/context-managers can be replaced by equivalent calls to
the context:

.. code-block:: diff

   -with tbot.acquire_lab() as lh:
   +with tbot.ctx.request(tbot.role.LabHost) as lh:
        lh.exec0("uname", "-a")

   -with tbot.acquire_local() as lo:
   +with tbot.ctx.request(tbot.role.LocalHost) as lo:
        lh.exec0("uname", "-a")

For some, you can simplify the code because prerequisites are acquired
automatically:

.. code-block:: diff

   -with tbot.acquire_lab() as lh:
   -    with tbot.acquire_board(lh) as b:
   +with tbot.ctx.request(tbot.role.Board) as b:
            ...

   -with tbot.acquire_lab() as lh:
   -    with tbot.acquire_board(lh) as b:
   -        with tbot.acquire_uboot(b) as ub:
   +with tbot.ctx.request(tbot.role.BoardUBoot) as ub:
                ub.exec0("version")

    # The above was also often done like this:
   -with contextlib.ExitStack() as cx:
   -    lh = cx.enter_context(tbot.acquire_lab())
   -    b = cx.enter_context(tbot.acquire_board(lh))
   -    ub = cx.enter_context(tbot.acquire_uboot(b))
   +with tbot.ctx.request(tbot.role.BoardUBoot) as ub:
        ub.exec0("version")

    # The same is true for board linux:
   -with contextlib.ExitStack() as cx:
   -    lh = cx.enter_context(tbot.acquire_lab())
   -    b = cx.enter_context(tbot.acquire_board(lh))
   -    lnx = cx.enter_context(tbot.acquire_linux(b))
   +with tbot.ctx.request(tbot.role.BoardLinux) as lnx:
        lnx.exec0("cat", "/etc/os-release")

The :py:func:`tbot.with_lab`, :py:func:`tbot.with_uboot`, and
:py:func:`tbot.with_linux` decorators do not have a direct replacement but
because acquring a machine from the context is a single line, the change is not
too big either:

.. code-block:: diff

    @tbot.testcase
   -@tbot.with_lab
   -def lab_name(lh):
   +def lab_name():
   +    with tbot.ctx.request(tbot.role.LabHost) as lh:
            lh.exec0("hostname")

    @tbot.testcase
   -@tbot.with_linux
   -def some_test_with_linux(lnx):
   +def some_test_with_linux():
   +    with tbot.ctx.request(tbot.role.BoardLinux) as lnx:
            lnx.exec0("cat", "/etc/os-release")

.. note::

   At some point, a new decorator to replace the existing ones might be
   introduced.  For the time being, the example above shows what needs to be done.

Migrating Configuration
^^^^^^^^^^^^^^^^^^^^^^^
While the old way of configuring tbot still works and is fully compatible with
the context API, it only provides limited possibilities.  For more complex
scenarios, the new :ref:`tbot_ctx_config` mechanism is much more flexible.

Switching over is not hard:  You need to define a ``register_machines()``
function in the lab- and/or board-config which replaces the existing ``LAB =``,
``BOARD =``, ``UBOOT =``, and ``LINUX =`` statements.  For the lab-config,
additionally, there is now a cleaner way to define the build-host:

.. code-block:: diff

    class MyBuildHost(...):
        ...

    class MyPersonalLab(...):
        ...

   -    def build(self):
   -        return MyBuildHost(self)

   -LAB = MyPersonalLab
   +def register_machines(ctx):
   +    ctx.register(MyPersonalLab, tbot.role.LabHost)
   +    ctx.register(MyBuildHost, tbot.role.BuildHost)

For the board-config it is even more straight-forward:

.. code-block:: diff

    class MyBoard(...):
        ...

    class MyUBoot(...):
        ...

    class MyBoardLinux(...):
        ...

   +def register_machines(ctx):
   -BOARD = MyBoard
   +    ctx.register(MyBoard, tbot.role.Board)
   -UBOOT = MyUBoot
   +    ctx.register(MyUBoot, tbot.role.BoardUBoot)
   -LINUX = MyBoardLinux
   +    ctx.register(MyBoardLinux, tbot.role.BoardLinux)
