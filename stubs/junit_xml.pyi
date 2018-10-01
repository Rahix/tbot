import typing

class TestCase:
    classname: str
    def __init__(
        self,
        name: str,
        classname: typing.Optional[str] = None,
        elapsed_sec: typing.Optional[float] = None,
        stdout: typing.Optional[str] = None,
        stderr: typing.Optional[str] = None,
        assertions: typing.Optional[str] = None,
        timestamp: typing.Optional[str] = None,
        status: typing.Optional[str] = None,
        category: typing.Optional[str] = None,
        file: typing.Optional[str] = None,
        line: typing.Optional[int] = None,
        log: typing.Optional[str] = None,
        group: typing.Optional[str] = None,
        url: typing.Optional[str] = None,
    ) -> None: ...

    def add_error_info(
        self,
        message: typing.Optional[str] = None,
        output: typing.Optional[str] = None,
        error_type: typing.Optional[str] = None,
    ) -> None: ...

class TestSuite:
    def __init__(
        self,
        name: str,
        test_cases: typing.Optional[typing.List[TestCase]] = None,
        hostname: typing.Optional[str] = None,
        id: typing.Optional[int] = None,
        package: typing.Optional[str] = None,
        timestamp: typing.Optional[str] = None,
        properties: typing.Optional[str] = None,
        file: typing.Optional[str] = None,
        log: typing.Optional[str] = None,
        url: typing.Optional[str] = None,
        stdout: typing.Optional[str] = None,
        stderr: typing.Optional[str] = None,
    ) -> None: ...

    @staticmethod
    def to_xml_string(
        test_suites: typing.List[TestSuite],
        pretty_print: bool = True,
        encoding: typing.Any = None,
    ) -> str: ...
