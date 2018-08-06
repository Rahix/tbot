from tbot.machine import channel
from tbot.machine import board


class DummyBoard(board.Board):
    def poweron(self) -> None:
        self.lh.exec0("ssh", "pollux", "remote_power", "fipad-b3", "on")

    def poweroff(self) -> None:
        self.lh.exec0("ssh", "pollux", "remote_power", "fipad-b3", "off")


class DummyBoardMachine(board.BoardMachine[DummyBoard]):
    name = "dummy-board"

    def connect(self) -> channel.Channel:
        chan = self.board.lh.new_channel()
        chan.send("rlogin metis -l fipad-b3\n")
        return chan


class DummyBoardUBoot(DummyBoardMachine, board.UBootMachine[DummyBoard]):
    prompt = "=> "


# class DummyBoardLinux(board.BoardLinux[DummyBoardMachine]):
#     ...
