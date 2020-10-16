.. _context:

Context
=======
The *context* is the new mechanism in tbot for managing machine instances.
Under the hood, the old configuration mechanism and the
:py:mod:`tbot.selectable` module are already using the context but using it
directly gives you even more power!

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
