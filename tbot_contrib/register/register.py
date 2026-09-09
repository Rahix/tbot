import tbot
import typing
import pickle
import os
from tbot.machine.shell import Shell
from tbot.machine import Machine, linux, board
import register


class Register:
    def __init__(self, name: str, address: int, width: int) -> None:
        self.name = name
        self.address = address
        assert width in [8, 16, 32, 64], f"Unsupported register width: {width!r}"
        self.width = width


class CPU:
    def __init__(
        self, host: Shell, processor_name: str = "", cpu_bits: int = 0
    ) -> None:
        self.set_host(host)
        if processor_name != "":
            THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
            file_name = os.path.join(THIS_FOLDER, f"{processor_name}.pkl")
            with open(file_name, "rb") as f:
                self._cpu_bits, self._groups_dict, self._registers_dict = pickle.load(f)

        elif cpu_bits > 0:
            assert cpu_bits in [32, 64], f"Unsupported register width: {cpu_bits!r}"
            self._cpu_bits = cpu_bits
            self._groups_dict = {}
            self._registers_dict = {}

        else:
            raise Exception(f"Wrong arguments")

    def __validate_host(self, host: Shell) -> None:
        self._host = host
        if isinstance(host, board.UBootShell):
            self._host_name = "uboot"

        elif isinstance(host, linux.LinuxShell):
            self._host_name = "linux"
        else:
            raise Exception(
                f"You are not in an allowed context (linux machine or uboot machine)"
            )

    def set_host(self, host: Shell) -> None:
        self.__validate_host(host)
        self._host = host

    def add_register_to_group(self, group_name: str, register: Register) -> None:
        if group_name in self._groups_dict:
            self._groups_dict[group_name].append(register.name)
            self._registers_dict[register.name] = register

        else:
            self._groups_dict[group_name] = []
            self._groups_dict[group_name].append(register.name)
            self._registers_dict[register.name] = register

    def remove_register_from_group(
        self, group_name: str, register_name: str
    ) -> Register:
        if not (group_name in self._groups_dict):
            raise Exception(f"There is not a group with the name: {group_name}")

        if not (register_name in self._groups_dict[group_name]):
            raise Exception(
                f"There is not a register with the name: {register_name} in the group: {group_name}"
            )

        self._groups_dict[group_name].remove(register_name)
        return self._registers_dict[register_name]

    def get_register_from_group(self, group_name: str, register_name: str) -> Register:
        if not (group_name in self._groups_dict):
            raise Exception(f"There is not a group with the name: {group_name}")

        if not (register_name in self._groups_dict[group_name]):
            raise Exception(
                f"There is not a register with the name: {register_name} in the group: {group_name}"
            )

        return self._registers_dict[register_name]

    def get_all_registers_from_group(self, group_name: str) -> typing.List[Register]:
        if not (group_name in self._groups_dict):
            raise Exception(f"There is not a group with the name: {group_name}")
        return list(self._groups_dict[group_name].values())

    def __bit_parser_kernel(self, width: int) -> str:
        if width > self._cpu_bits:
            raise Exception(f"Maximun register width is: {self._cpu_bits}")

        if width == 8:
            return "b"
        elif width == self._cpu_bits:
            return "w"
        elif width == (self._cpu_bits / 2):
            return "h"
        else:
            raise Exception(f"Not a valid width")

    def __bit_parser_uboot(self, width: int) -> typing.Tuple[str, int]:
        if width > self._cpu_bits:
            raise Exception(f"Maximun register width is: {self._cpu_bits}")

        if width == 8:
            return ".b", 1
        elif width == 16:
            return ".w", 1
        elif width == 32:
            return ".l", 1
        elif width > 32:
            i = width / 32
            return ".l", int(i)

    def __validate_register_address_alignment(self, register: Register) -> bool:
        address = str(hex(register.address))
        multiple_word = self._cpu_bits / 8
        multiple_halfword = multiple_word / 2
        if register.width == 8:
            return True
        elif register.width == self._cpu_bits:
            if (int(address[-1], 16) % multiple_word) == 0:
                return True
        elif register.width == (self._cpu_bits / 2):
            if (int(address[-1], 16) % multiple_halfword) == 0:
                return True
        return False

    def read_register(self, register_name: str) -> None:
        if not (register_name in self._registers_dict):
            raise Exception(f"There is not a register with the name: {register_name}")

        if self.__validate_register_address_alignment(
            self._registers_dict[register_name]
        ):
            if self._host_name == "linux":
                self._host.exec(
                    "devmem2",
                    str(hex(self._registers_dict[register_name].address)),
                    self.__bit_parser_kernel(self._registers_dict[register_name].width),
                )
            elif self._host_name == "uboot":
                l, m = self.__bit_parser_uboot(
                    self._registers_dict[register_name].width
                )
                command = "md" + l
                for i in range(0, m):
                    if i == 0:
                        self._host.exec(
                            command,
                            str(hex(self._registers_dict[register_name].address)),
                            "1",
                        )
                    else:
                        # it needs work.
                        self._host.exec(command)
        else:
            tbot.log.message(
                f"The register: {self._registers_dict[register_name].name} has an unaligned address: {hex(self._registers_dict[register_name].address)} with width: {self._registers_dict[register_name].width}"
            )

    def read_all_registers_from_group(self, group_name: str) -> None:
        if not (group_name in self._groups_dict):
            raise Exception(f"There is not a group with the name: {group_name}")
        if self._groups_dict[group_name] == []:
            raise Exception(f"The group: {group_name} is empty")

        for register_name in self._groups_dict[group_name]:
            self.read_register(register_name)

    def write_register(self, register_name: str, value: int) -> None:
        if not (register_name in self._registers_dict):
            raise Exception(f"There is not a register with the name: {register_name}")

        if self.__validate_register_address_alignment(
            self._registers_dict[register_name]
        ):
            if self._host_name == "linux":
                self._host.exec(
                    "devmem2",
                    hex(self._registers_dict[register_name].address),
                    self.__bit_parser_kernel(self._registers_dict[register_name].width),
                    hex(value),
                )
            elif self._host_name == "uboot":
                l, m = self.__bit_parser_uboot(
                    self._registers_dict[register_name].width
                )
                command = "mw" + l
                for i in range(0, m):
                    if i == 0:
                        self._host.exec(
                            command,
                            hex(self._registers_dict[register_name].address),
                            hex(value),
                            "1",
                        )
                    else:
                        # it needs work.
                        self._host.exec(command)
        else:
            tbot.log.message(
                f"The register: {self._registers_dict[register_name].name} has an unaligned address: {hex(self._registers_dict[register_name].address)} with width: {self._registers_dict[register_name].width}"
            )
