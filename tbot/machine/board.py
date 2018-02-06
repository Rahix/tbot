from . import machine

class MachineBoard(machine.Machine):
    @property
    def common_machine_name(self) -> str:
        return "board"
