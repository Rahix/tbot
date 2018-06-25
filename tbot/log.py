"""
TBot logging facilities
-----------------------
"""
import sys
import enum
import json
import time
import typing
import pathlib


def has_unicode(with_unicode: str, without_unicode: str) -> str:
    """
    Check whether the terminal supports unicode, if it does,
    returns the ``with_unicode`` string, if it doesn't, returns
    the ``without_unicode`` string.

    :param str with_unicode: String to be returned, if the terminal does
                         support unicode
    :param str without_unicode: String to be returned, if the terminal does
                            not support unicode
    :rtype: str
    """
    if sys.stdout.encoding == "UTF-8":
        return with_unicode
    return without_unicode


def has_color(seq: str) -> str:
    """
    Check color support and return the escape sequence for this color
    code if enabled.

    :param str seq: The color code, eg ``"1;31"``
    :rtype: str
    """
    if True:
        return f"\x1B[{seq}m"
    return ""


class Verbosity(enum.IntEnum):
    """ Logger verbosity level """
    ALL = -1
    ERROR = 0
    WARNING = 1
    INFO = 2
    DEBUG = 3
    VERBOSE = 4
    VERY_VERBOSE = 5
    OVER_VERBOSE = 6
    NEVER = 1000000

    def __str__(self) -> str:
        return super(Verbosity, self).__str__().split(".")[-1]


LOGFILE = None
LOGLIST = list()
LOGVERBOSITY = Verbosity.WARNING
LOGNESTLAYER = 0
LOG_DO_DOC = True


def check_log() -> None:
    """
    Check whether the log has been initialized and throw an exception
    otherwise.
    """
    global LOGFILE  # pylint: disable=global-statement
    if LOGFILE is None:
        raise Exception("Logfile was not initialized!")


class LogStdoutHandler:
    """
    Handler for writing to stdout and dealing with a logevent after
    it's creation. You should not need to instanciate this object yourself,
    use :func:`tbot.log.event`.

    :ivar dct: The log event's dictionary, you can add additional things
    :ivar key: Key in the dictionary that output given to `.print()` should
               be appended to.
    :ivar prefix: A custom prefix that will be added in front of continuation
                  lines.
    """

    def __init__(
        self,
        dct: typing.Dict[str, typing.Any],
        verbosity: Verbosity,
        custom_dash: typing.Optional[str],
    ) -> None:
        global LOGVERBOSITY  # pylint: disable=global-statement
        global LOGNESTLAYER  # pylint: disable=global-statement
        self.do_output = verbosity <= LOGVERBOSITY
        self.is_continuation = False
        self.layer = LOGNESTLAYER
        self.custom_dash = custom_dash
        self.dct = dct
        self.key: typing.Optional[str] = None
        self.prefix: typing.Optional[str] = None

    def reset_verbosity(self, new_verbosity: Verbosity) -> None:
        """
        Change the verbosity of this log event

        :param Verbosity new_verbosity: The new verbosity
        """
        global LOGVERBOSITY  # pylint: disable=global-statement
        self.do_output = new_verbosity <= LOGVERBOSITY

    def print(self, msg: str) -> None:
        """
        Print some text to stdout provided the verbosity is high enough.
        Also, add the text to the dict in case a `key` was set.

        :param str msg: The text
        """
        # Add to log event
        if self.key is not None:
            if msg == "":
                self.dct[self.key] += "\n"
            else:
                self.dct[self.key] += msg + ("" if msg[-1] == "\n" else "\n")

        if not self.do_output:
            return
        lines = msg.split("\n")

        for line in lines:
            msg_prefix = has_color("0")
            prfx = has_unicode("│   ", "|   ")
            for _ in range(0, self.layer):
                msg_prefix += prfx
            if not self.is_continuation:
                if self.custom_dash is not None:
                    msg_prefix += self.custom_dash
                else:
                    msg_prefix += has_unicode("├─", "+-")
                self.is_continuation = True
            else:
                msg_prefix += has_unicode("│ ", "| ")
                if self.prefix is not None:
                    msg_prefix += self.prefix
            print(msg_prefix + line + has_color("0"))


def event(
    ty: typing.List[str],
    *,
    msg: typing.Optional[str] = None,
    verbosity: Verbosity = Verbosity.INFO,
    dct: typing.Optional[typing.Dict[str, typing.Any]] = None,
    custom_dash: typing.Optional[str] = None,
    fake: bool = False,
) -> LogStdoutHandler:
    """
    Create a new log event

    :param list[str] ty: The type of this log event
    :param str msg: An optional message intended for being printed on the screen
    :param Verbosity verbosity: Optional verbosity of this event (defaults to ``INFO``)
    :param dict dct: A dictionary of payload for this logevent. Can't contain keys
                named ``"type"``, ``"time"``, ``"message"``, or ``"verbosity"``.
    :param str custom_dash: Different prefix for the message when printed onscreen
    :param bool fake: Whether this is just a fake event that won't be logged
    :returns: A handler for the created log event
    :rtype: LogStdoutHandler
    """
    global LOGLIST  # pylint: disable=global-statement
    check_log()
    dct = dct or dict()

    forbidden = ["type", "time", "message", "verbosity"]

    for itm in forbidden:
        if itm in dct:
            raise Exception(f"A log event can not contain items named '{itm}'!")

    dct["type"] = ty
    dct["time"] = time.ctime()
    dct["verbosity"] = str(verbosity)

    stdout_handler = LogStdoutHandler(dct, verbosity, custom_dash)
    if msg is not None:
        dct["message"] = msg
        stdout_handler.print(msg)

    if not fake:
        LOGLIST.append(dct)

    return stdout_handler


def message(msg: str, verbosity: Verbosity = Verbosity.INFO) -> LogStdoutHandler:
    """
    Print a message

    :param str msg: The message
    :param Verbosity verbosity: Optional verbosity for this message
    :returns: A handler for the created log event
    :rtype: LogStdoutHandler
    """
    return event(
        ty=["msg", str(verbosity)], msg=msg, verbosity=verbosity, dct={"text": msg}
    )


def doc(text: str) -> LogStdoutHandler:
    """
    Add a log event that contains text for the documentation generator.
    ``text`` should be formatted in Markdown.

    :param str text: The documentation fragment
    :returns: A handler for the created log event
    :rtype: LogStdoutHandler
    """
    return event(
        ty=["doc", "text"],
        verbosity=Verbosity.NEVER,
        dct={"text": text},
        fake=not LOG_DO_DOC,
    )


def doc_appendix(title: str, text: str) -> LogStdoutHandler:
    """
    Add a log event that contains an appendix for the documentation generator.
    ``text`` should be formatted in Markdown.

    :param str title: The appendix's title
    :param str text: The appendix's body
    :returns: A handler for the created log event
    :rtype: LogStdoutHandler
    """
    return event(
        ty=["doc", "appendix"],
        verbosity=Verbosity.NEVER,
        dct={"title": title, "text": text},
        fake=not LOG_DO_DOC,
    )


def debug(msg: str) -> LogStdoutHandler:
    """
    Print a debug message

    :param str msg: The message
    :returns: A handler for the created log event
    :rtype: LogStdoutHandler
    """
    return message(msg, Verbosity.DEBUG)


def oververbose(msg: str) -> LogStdoutHandler:
    """
    Log a "oververbose" message, this is intended for very rarely needed debug
    output (just run TBot with this verbosity and see for yourself ...)

    Will not create a new log event.

    :param str msg: The message
    :returns: A handler for the message
    :rtype: LogStdoutHandler
    """
    stdout_handler = LogStdoutHandler(
        dict(), Verbosity.OVER_VERBOSE, has_unicode("├>", "+>")
    )
    stdout_handler.print(has_color("33") + msg)
    return stdout_handler


def set_layer(layer: int) -> None:
    """
    Set the call graph depth.
    You should never need to call this yourself.
    """
    global LOGNESTLAYER  # pylint: disable=global-statement
    LOGNESTLAYER = layer


def init_log(
    filename: typing.Union[pathlib.Path, str], verbosity: Verbosity = Verbosity.INFO
) -> None:
    """
    Initialize the logger

    :param filename: The file the log should be written to (in json format)
    :type filename: pathlib.Path or str
    :param Verbosity verbosity: The minimun verbosity for messages that are printed
                      to stdout
    """
    global LOGFILE  # pylint: disable=global-statement
    global LOGVERBOSITY  # pylint: disable=global-statement
    LOGFILE = pathlib.Path(filename)
    LOGVERBOSITY = verbosity


def flush_log() -> None:
    """
    Write the log file
    """
    global LOGLIST  # pylint: disable=global-statement
    global LOGFILE  # pylint: disable=global-statement
    check_log()
    if LOGFILE is not None:
        json.dump(LOGLIST, open(LOGFILE, "w"), indent=4)
