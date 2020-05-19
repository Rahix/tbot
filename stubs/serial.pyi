import typing

PARITY_NONE: str
PARITY_EVEN: str
PARITY_ODD: str
PARITY_MARK: str
PARITY_SPACE: str

STOPBITS_ONE: float
STOPBITS_ONE_POINT_FIVE: float
STOPBITS_TWO: float

FIVEBITS: int
SIXBITS: int
SEVENBITS: int
EIGHTBITS: int

class Serial:
    def __init__(
        self,
        port: typing.Optional[str] = None,
        baudrate: int = 9600,
        bytesize: int = 0,
        parity: str = "",
        stopbits: float = 0,
        timeout: typing.Optional[float] = None,
        xonoff: bool = False,
        rtscts: bool = False,
        dsrdtr: bool = False,
        write_timeout: typing.Optional[float] = None,
        inter_byte_timeout: typing.Optional[float] = None,
        exclusive: bool = False,
    ): ...
    def open(self) -> None: ...
    def close(self) -> None: ...
    def read(self, size: int = 1) -> bytes: ...
    def read_until(
        self, expected: bytes = b"\n", size: typing.Optional[int] = None
    ) -> bytes: ...
    def write(self, data: bytes) -> int: ...
    def flush(self) -> None: ...
    def fileno(self) -> int: ...
    @property
    def in_waiting(self) -> int: ...
    @property
    def out_waiting(self) -> int: ...
    def reset_input_buffer(self) -> None: ...
    def reset_output_buffer(self) -> None: ...
    def send_break(self, duration: float = 2.5) -> None: ...
    break_condition: bool
    rts: bool
    dtr: bool
    @property
    def name(self) -> str: ...
    @property
    def cts(self) -> bool: ...
    @property
    def dsr(self) -> bool: ...
    @property
    def ri(self) -> bool: ...
    @property
    def cd(self) -> bool: ...
    @property
    def is_open(self) -> bool: ...
    port: str
    baudrate: int
    bytesize: int
    parity: str
    stopbits: float
    timeout: typing.Optional[float]
    write_timeout: typing.Optional[float]
    inter_byte_timeout: typing.Optional[float]
    xonoff: bool
    rtscts: bool
    dsrdtr: bool
