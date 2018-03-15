.. tbot logging

TBot logging
============

tbot log file ``log.json``
--------------------------

tbot create a ``log.json`` file when run. This file contains detailed information about what
happened while running. It is structured as a json array of dictionaries containing information
about events in the order they happened. An event might look like this::

    {
        "name": "selftest",
        "type": [
            "testcase",
            "begin"
        ],
        "time": "Thu Jan 25 09:49:30 2018"
    }

or this::

    {
        "success": true,
        "type": ["tbotend"],
        "time": "Thu Jan 25 09:49:39 2018"
    }

Each event has at least a ``"type"`` being an array of strings and a ``"time"``,
as an ``asctime()``. Other keys may exist, depending on the event type. The following event types exist
(But you can add your own, of course):

* ``["testcase", "begin"]``: Start of a testcase, contains no further information than the testcase's ``"name"``.
* ``["testcase", "end"]``: End of a testcase, contains ``"name"`` and ``"duration"`` of the testcase and whether
  it returned with ``"success"`` (= no exception was thrown).
* ``["shell", ...]``: A shell command was executed. Contains the ``"command"``, its ``"exit_code"`` and
  ``"output"``, a hint, whether documentation generation should include the command (``"show"``) and whether
  the output should be included (``"show_stdout"``). ``["type"][1:]`` is the shelltype.
* ``["doc", "text"]``: A text message to be included in the tbot log. Conventionally this is interpreted as
  Markdown. ``"text"`` contains the actual message.
* ``["doc", "appendix"]``: An appendix to be added to the end of a documentation. For example a file needed for
  repeating the test run. Has a ``"title"`` and a ``"text"``.
* ``["board", "powerup"]``: Marker that the board was powered on at this point, ``"board"`` contains the name of
  the board. Usually followed by a shell event with the command used to do so.
* ``["board", "boot"]``: Boot ``"log"`` of powering on the board.
* ``["board", "poweroff"]``: Marker that the board was powered off at this point. ``"board"`` contains the name of
  the board. Usually followed by a shell event with the command used to do so.
* ``["exception"]``: An exception occured at this point. This is not necessarily fatal, in some cases it even is required
  for a testcase to succeed. Contains the exceptions ``"name"`` and a ``"trace"``.
* ``["msg", verbosity]``: A ``"text"`` message. ``verbosity`` is the Verbosity level.
* ``["tbotend"]``: The very last event. Only information is, whether the test run was a ``"success"``.

As a demonstration of how this log might be used, take a look at the generate scripts:

.. automodule:: generators.generate_documentation
   :members:

.. automodule:: generators.generate_htmllog
   :members:
