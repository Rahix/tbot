from . import machine

class MachineBoard(machine.Machine):
    @property
    def common_machine_name(self):
        return "board"
