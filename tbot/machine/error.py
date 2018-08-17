class CommandFailedException(Exception):
    def __init__(self, host, command, stdout, *args) -> None:
        super().__init__(*args)
        self.host = host
        self.command = command
        self.stdout = stdout

    def __str__(self) -> str:
        return f"[{self.command}] failed!"
