.. py:module:: tbot.machine.channel

``tbot.machine.channel``
========================
The :py:mod:`~tbot.machine.channel` module provides the low-level
implementation if interaction with machine.  A channel is analogous to a serial
connection: You can send and receive bytes.  This 'raw' interface is abstracted
as a :py:class:`~tbot.machine.channel.ChannelIO`, for which there are multiple
:ref:`chanio_impls`.

``Channel`` class
-----------------
The channel class has multiple different interfaces at different levels of
abstraction which allow interacting with the underlying 'raw' channel.  These
are:

- **Byte-level interface**: The :py:meth:`~tbot.machine.channel.Channel.write`
  and :py:meth:`~tbot.machine.channel.Channel.read` methods allow the most
  basic interaction.  For a bit more ergonomic use, there is also a
  :py:meth:`~tbot.machine.channel.Channel.read_iter`.
- **Log-stream interface**: For interaction with the :py:mod:`tbot.log` module
  and to allow capturing the entire received data in parallel to interfacing
  with the remote, channels provide the
  :py:meth:`~tbot.machine.channel.Channel.with_stream` context manager.
- **Death-strings**: 'Death-strings' are strings (or regular expressions),
  which should never appear on the channel and when they do, an exception will
  be raised.  In an embedded setting, it might make sense to add the
  kernel-panic header as a death-string, for example.  For this purpose, the
  :py:meth:`~tbot.machine.channel.Channel.with_death_string` context-manager is
  provided.
- **pexpect interface**: tbot's channel implementation also has methods
  mimicking the pexpect interface.  These are:

  - :py:meth:`~tbot.machine.channel.Channel.send`
  - :py:meth:`~tbot.machine.channel.Channel.sendline`
  - :py:meth:`~tbot.machine.channel.Channel.sendintr`
  - :py:meth:`~tbot.machine.channel.Channel.readline`

- **Prompt handling**: The :py:meth:`~tbot.machine.channel.Channel.read_until_prompt`
  method allows waiting for a prompt string to appear.  A global prompt-string
  can be configured with :py:meth:`~tbot.machine.channel.Channel.with_prompt`.
- **Borrowing & taking**: To model ownership of the channel, the
  :py:meth:`~tbot.machine.channel.Channel.borrow` context-handler allows
  creating a copy of the channel which temporarily holds exclusive access to
  it.  This ensures that all references to the old channel are blocked for the
  duration of the borrow.  :py:meth:`~tbot.machine.channel.Channel.take` does
  the same thing but permanently moves ownership.
- **Interactive Mode**: Using
  :py:meth:`~tbot.machine.channel.Channel.attach_interactive`, an interactive
  session with this channel can be started.

.. autoclass:: tbot.machine.channel.Channel
   :members:

.. _channel_search_string:

Search Strings
--------------
A lot of channel methods are marked to take a :py:class:`ConvenientSearchString`:

.. py:class:: ConvenientSearchString

This is just an 'umbrella' above a few different possible types which can be
passed in here:

- :py:class:`bytes`: Will be matched literally.
- :py:class:`str`: Will be encoded as UTF-8 and the resulting bytes are matched literally.
- *Compiled Regex Pattern*: An ``re`` **byte**-pattern with a bounded
  length can also be passed in.  The bounded length is required for efficient
  searching.  This means, instead of ``.*`` you need to match a maximum number
  of chars like ``.{0,80}``.

**Example**:

.. code-block:: python

   import re

   # A `str` or `bytes` object will be matched literally
   with chan.with_death_string("Kernel panic - not syncing: "):
      ...

   # A regexp pattern (byte-pattern!)
   pat = re.compile(b"[a-zA-Z0-9-]{1,80} login: ")
   chan.read_until_prompt(pat)

.. _chanio_impls:

Implementations
---------------
.. autoclass:: tbot.machine.channel.SubprocessChannel

   A channel based on opening a shell in a subprocess.

.. autoclass:: tbot.machine.channel.ParamikoChannel

   A channel based on opening an SSH-connection via paramiko.

``ChannelIO`` interface
-----------------------
This is the interface each channel implementation needs to implement.  The
actual channel class is just a wrapper ontop of it.

.. autoclass:: tbot.machine.channel.ChannelIO
   :members:
