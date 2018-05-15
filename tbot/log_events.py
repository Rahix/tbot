import tbot

RST = tbot.log.has_color("0")
BRED = tbot.log.has_color("1;31")
BGREEN = tbot.log.has_color("1;32")
BYELLOW = tbot.log.has_color("1;33")
BBLUE = tbot.log.has_color("1;34")

DASH_END = tbot.log.has_unicode("└─", "\\-")

def testcase_begin(name):
    tbot.log.event(
        ty=["testcase", "begin"],
        msg=f"Calling {BBLUE}{name}{RST} ...",
        verbosity=tbot.log.Verbosity.ALL,
        dct={
            "name": name,
        },
    )

def testcase_end(name, duration, success=True, fail_ok=False):
    if success:
        message = BGREEN + "Done."
    else:
        if fail_ok:
            message = BYELLOW + "Fail expected."
        else:
            message = BRED + "Fail."
    tbot.log.event(
        ty=["testcase", "end"],
        msg=message,
        verbosity=tbot.log.Verbosity.ALL,
        dct={
            "name": name,
            "duration": duration,
            "success": success,
            "fail_ok": success,
        },
        custom_dash=DASH_END,
    )

def tbot_done(success):
    message = f"Done, {BGREEN if success else BRED}{'SUCCESS' if success else 'FAILURE'}"
    tbot.log.event(
        ty=["tbot", "end"],
        msg=message,
        verbosity=tbot.log.Verbosity.ALL,
        dct={
            "success": success,
        },
    )

def exception(name: str, trace: str):
    tbot.log.event(
        ty=["exception"],
        msg=f"Catched exception: {name}",
        verbosity=tbot.log.Verbosity.DEBUG,
        dct={
            "name": name,
            "trace": trace,
        },
    )
