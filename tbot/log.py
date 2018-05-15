"""
TBot logging facilities
-----------------------
"""
import sys
import enum
import json
import time
import pathlib

def has_unicode(with_unicode: str, without_unicode: str) -> str:
    """
    Check whether the terminal supports unicode, if it does,
    returns the ``with_unicode`` string, if it doesn't, returns
    the ``without_unicode`` string.

    :param with_unicode: String to be returned, if the terminal does
                         support unicode
    :type with_unicode: str
    :param without_unicode: String to be returned, if the terminal does
                            not support unicode
    :type without_unicode: str
    :rtype: str
    """
    if sys.stdout.encoding == "UTF-8":
        return with_unicode
    return without_unicode

def has_color(seq: str) -> str:
    if True:
        return f"\x1B[{seq}m"
    else:
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

    def __str__(self) -> str:
        return super(Verbosity, self).__str__().split(".")[-1]

LOGFILE = None
LOGLIST = list()
LOGVERBOSITY = Verbosity.WARNING
LOGNESTLAYER = 0

def check_log():
    global LOGFILE #pylint: disable=global-statement
    if LOGFILE is None:
        raise Exception("Logfile was not initialized!")

class LogStdoutHandler:

    def __init__(self, dct, verbosity, custom_dash):
        global LOGVERBOSITY #pylint: disable=global-statement
        global LOGNESTLAYER #pylint: disable=global-statement
        self.do_output = verbosity <= LOGVERBOSITY
        self.is_continuation = False
        self.layer = LOGNESTLAYER
        self.custom_dash = custom_dash
        self.dct = dct
        self.key = None
        self.prefix = None

    def reset_verbosity(self, new_verbosity):
        global LOGVERBOSITY #pylint: disable=global-statement
        self.do_output = new_verbosity <= LOGVERBOSITY

    def print(self, msg: str):
        if not self.do_output:
            return
        lines = msg.split("\n")

        # Add to log event
        if self.key is not None:
            if msg == "":
                self.dct[self.key] += '\n'
            else:
                self.dct[self.key] += msg + ('' if msg[-1] == '\n' else '\n')

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

def event(ty, *,
          msg = None,
          verbosity = Verbosity.INFO,
          dct = None,
          custom_dash = None,
         ):
    global LOGLIST #pylint: disable=global-statement
    check_log()
    dct = dct or dict()

    forbidden = ['type', 'time', 'message', 'verbosity']

    for itm in forbidden:
        if itm in dct:
            raise Exception(f"A log event can not contain items named '{itm}'!")

    dct['type'] = ty
    dct['time'] = time.ctime()
    dct['verbosity'] = str(verbosity)

    stdout_handler = LogStdoutHandler(dct, verbosity, custom_dash)
    if msg is not None:
        dct['message'] = msg
        stdout_handler.print(msg)

    LOGLIST.append(dct)

    return stdout_handler

def message(msg, verbosity=Verbosity.INFO):
    return event(
        ty=["msg", str(verbosity)],
        msg=msg,
        verbosity=verbosity,
        dct={
            "text": msg,
        },
    )

def debug(msg):
    return message(msg, Verbosity.DEBUG)

def set_layer(layer):
    global LOGNESTLAYER #pylint: disable=global-statement
    LOGNESTLAYER = layer

def init_log(filename, verbosity = Verbosity.INFO):
    global LOGFILE #pylint: disable=global-statement
    global LOGVERBOSITY #pylint: disable=global-statement
    #TODO: Remove .2
    LOGFILE = pathlib.Path(str(filename) + ".2")
    LOGVERBOSITY = verbosity

def flush_log():
    global LOGLIST #pylint: disable=global-statement
    global LOGFILE #pylint: disable=global-statement
    check_log()
    json.dump(LOGLIST,
              open(LOGFILE, "w"),
              indent=4)
