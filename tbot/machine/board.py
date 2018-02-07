"""
Abstract base class for board machines
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
"""
from . import machine

# TODO: Handle board log events in here

class MachineBoard(machine.Machine):
    """ Abstract base class for board machines """
    @property
    def common_machine_name(self) -> str:
        """ Common name of this machine, for boards this will always be ``"board"`` """
        return "board"
