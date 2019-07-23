import re
from .. import channel


def wait_for_shell(ch: channel.Channel) -> None:
    # Repeatedly sends `echo TBOT''LOGIN\r`.  At some point, the shell
    # interprets this command and prints out `TBOTLOGIN` because of the
    # quotation-marks being removed.  Once we detect this, this function
    # can return, knowing the shell is now running on the other end.
    #
    # Credit to Pavel for this idea!
    with ch.with_prompt(re.compile(b"TBOTLOGIN.{0,80}", re.DOTALL)):
        while True:
            ch.sendline("echo TBOT''LOGIN")
            try:
                ch.read_until_prompt(timeout=0.2)
                break
            except TimeoutError:
                pass
