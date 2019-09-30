.. _logging:

Logging
=======
tbot can keep record of test-runs in a log-file.  For this, entries detailing a number of events
will be stored:

* Testcase begin and end, their duration and success state.
* All commands which are run, their output, return-code, and on which machine they were run.
* Custom messages and events emitted by testcases (for example by using
  :py:func:`tbot.log.message`).

To enable logging, set either the ``--log=<file.json>`` or the ``--log-auto`` parameter.  The latter
will automatically create a log-file in ``log/<lab>-<board>-NNNN.json``, ``NNNN`` incrementing so
old files are not overwritten.

The log format is a stream of json objects.  To read it, you can use the ``generators/logparser.py``
module.

.. warning::

   A json stream is **not** just a json file.  This means trying to parse the log-file as plain json
   will fail!  Use the provided log-parser instead.

Generators
----------
One use of the log is generating visualizations and statistics of a test run.  There are a few so
called *generators* already included with tbot:

* ``generators/dot.py``: Generate a graphviz dot graph of the testcase hirarchy that was run.
* ``generators/htmllog.py``: Generate a html representation of the log that gives an overview
  of the occurences that happened during the run.
* ``generators/junit.py``: Convert the log to a `JUnit <https://junit.org/junit5/>`_ xml file which
  can be displayed by CI tools like Jenkins.
* ``generators/messages.py``: A simple demo generator that just prints all message events.

Log Events
----------
Log events are json objects.  Each one has at least the following fields:

* ``"type"``: An array that identifies the event type.  Events for similar occurences have a common
  prefix in the ``type`` array.
* ``"time"``: Time in seconds since the test run began.
* ``"data"``: An object with event specific elements.

The following events are emitted by tbot (possibly incomplete):

* ``["tc", "begin"]`` - Testcase being called, ``data`` contains the ``"name"``.
* ``["tc", "end"]`` - Testcase ending, ``data`` holds the ``"name"``, ``"duration"``, and
  ``"success"`` state.
* ``["cmd", "<machine-name>"]`` - A command was issued on the specified machine.  ``data`` is filled
  with the ``"cmd"`` that was sent and its ``"stdout"``.
* ``["msg", "<LEVEL>"]`` - A log message at the specified level, ``data`` contains the ``"text"``.
* ``["tbot", "end"]`` - Emitted once after all testcases completed (or failed).  ``data`` knows about
  the total ``"duration"`` and overall ``"success"``.

More might be added in the future.
