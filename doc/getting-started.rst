.. highlight:: guess
   :linenothreshold: 3

Getting Started
===============

First Steps
-----------
TBot works out of the box. You can run it's selftests like this::

    ~$ tbot selftest

(If this does not work, please contact the developers. This should not be the case)

Now, let's create some example testcase. Start by creating a file named ``tc.py`` in
your current directory. Later you will see that you can also name it differently or
have multiple files, but for now, this is the easiest way. Add the following content::

    import tbot

    @tbot.testcase
    def my_awesome_testcase() -> None:
        with tbot.acquire_lab() as lh:
            name = lh.exec0("uname", "-n")
            tbot.log.message(f"Hello {name}!")

If you did everything correctly, running

::

    ~$ tbot my_awesome_testcase


.. highlight:: python
   :linenothreshold: 3

should greet you host. Let's disect the code from above::

    @tbot.testcase
    def my_awesome_testcase() -> None:
        ...

This is just a normal python function for our testcase. The ``tbot.testcase``
decorator tells TBot that it should be treated as a testcase. In practice this
means that TBot will allow calling it from the commandline and will hook into
the call so it can gather log data about it.

::

    with tbot.acquire_lab() as lh:
        ...

To understand this line, we first need to get to know one of the core concepts of TBot:
**Machines**. Every host TBot interacts with is called a machine. That includes the labhost,
which we use here, a buildhost where your code might be compiled, the board you are testing,
or any other host you want TBot to connect to. There are different kinds of machine. Our
labhost is special, because it is the base from where connections to other host are made.
This allows TBot to only need one connection to one host for doing its task.

Machines should always be used inside a ``with`` statement to ensure proper cleanup in any
case. This is especially important with boardmachines, because if this is not done, the board
might not be turned off after the tests.

So, the line you see here requests a new labhost object from TBot so we can interact with it.
As you will see later, this is not quite the way you would do this normally, but for this simple
example it is good enough.

::

    name = lh.exec0("uname", "-n")

Now that we have the ability to interact with the labhost, let's do so: We call ``uname -n`` to
greet the users machine. Note, that each argument is passed separately to ``exec0``. The reason
for this is that it ensures everything will be properly escaped and there are no accidental mistakes.
For special characters there is a different notation as you will see later.

::

    tbot.log.message(f"Hello {name}!")

This is basically TBot's equivalent of ``print``. The most important difference is, that it does not
only print it to the terminal, but also store it in the logfile.

.. todo::
    Verbosity

Writing Testcases
-----------------
As mentioned above, testcases calling ``acquire_lab`` is not the best way to do it. Why? Well, imagine,
each testcase that is called would create a new ssh connection to your labhost. This would be really
inefficient. The easiest solution is to require the lab as a parameter like this::

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
            name = lh.exec0("uname", "-n")
            tbot.log.message(f"Hello {name}!")

I'd suggest remembering this and using it for any testcase that should be commandline callable.

.. note::
    In this documentation and in the TBot sources, type annotations are used everywhere. This allows
    the use of a static type-checker such as ``mypy``, which makes finding bugs before you even run
    the code a lot easier. Of course, this is optional, the following code would work just as well::


        import tbot

        @tbot.testcase
        def my_testcase(lab = None) -> None:
            with lab or tbot.acquire_lab() as lh:
                name = lh.exec0("uname", "-n")
                tbot.log.message(f"Hello {name}!")
