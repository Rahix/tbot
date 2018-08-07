from tbot.machine import channel
from tbot.machine import board


class DummyBoard(board.Board):
    def poweron(self) -> None:
        self.lh.exec0("ssh", "pollux", "remote_power", "at91sam9g45", "on")

    def poweroff(self) -> None:
        self.lh.exec0("ssh", "pollux", "remote_power", "at91sam9g45", "off")


class DummyBoardMachine(board.BoardMachine[DummyBoard]):
    name = "dummy-board"

    def connect(self) -> channel.Channel:
        chan = self.board.lh.new_channel()
        chan.send("rlogin ts3 -l at91sam9g45\n")
        return chan


class DummyBoardUBoot(DummyBoardMachine, board.UBootMachine[DummyBoard]):
    prompt = "U-Boot> "


# class DummyBoardLinux(board.BoardLinux[DummyBoardMachine]):
#     ...
