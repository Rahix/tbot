""" Base class for board shells """
import abc
import tbot.shell


class BoardShell(tbot.shell.Shell):
    """ Base class for board shells """
    @abc.abstractmethod
    def _cleanup_boardstate(self):
        """ Make sure, the board is in a known state (poweroff) """
        pass

    @abc.abstractmethod
    def _board_shell_type(self):
        """ Return the boardshell type to identify this shell """
        pass

    @abc.abstractmethod
    def poweron(self):
        """ Poweron the board """
        pass

    def _shell_type(self):
        shell_type = ["board"]
        shell_type.extend(self._board_shell_type())

        return tuple(shell_type)
