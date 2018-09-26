import json
import pathlib
import time
import typing


class LogFileWriter:

    def __init__(self, path: pathlib.Path) -> None:
        self.file = path.open("w")
        self.start = time.monotonic()

    def event(self, ty: typing.List[str], data: typing.Dict) -> None:
        ev = {"type": ty, "time": time.monotonic() - self.start, "data": data}

        json.dump(ev, self.file, indent=2)
        self.file.write("\n")
        self.file.flush()
