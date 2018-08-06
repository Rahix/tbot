from tbot.machine import channel
from tbot.machine import board


class DummyBoard(board.Board):
    def poweron(self) -> None:
        self.lh.exec0("ssh", "pollux", "remote_power", "harald-desk", "on")

    def poweroff(self) -> None:
        self.lh.exec0("ssh", "pollux", "remote_power", "harald-desk", "off")


class DummyBoardMachine(board.BoardMachine[DummyBoard]):
    name = "dummy-board"

    def connect(self) -> channel.Channel:
        chan = self.board.lh.new_channel()
        chan.send("sh\n")
        return chan


# class DummyBoardUBoot(board.BoardUBoot[DummyBoardMachine]):
#     ...
#
#
# class DummyBoardLinux(board.BoardLinux[DummyBoardMachine]):
#     ...
