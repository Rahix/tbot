import typing
import socket

class Channel:
    def exec_command(self, command: str) -> None: ...
    def recv(self, nbytes: int) -> bytes: ...
    def recv_exit_status(self) -> int: ...

class Transport:
    def open_session(
        self,
        window_size: typing.Optional[int] = None,
        max_packet_size: typing.Optional[int] = None,
        timeout: typing.Optional[float] = None,
    ) -> Channel: ...

class SSHClient:
    def load_system_host_keys(self) -> None: ...
    def connect(
        self,
        hostname: str,
        port: int = 22,
        username: typing.Optional[str] = None,
        password: typing.Optional[str] = None,
        passphrase: typing.Optional[str] = None,
        # pkey: typing.Optional[typing.Any] = None,
        key_filename: typing.Optional[str] = None,

        timeout: typing.Optional[float] = None,
        allow_agent: bool = True,
        look_for_keys: bool = True,
        compress: bool = False,
        sock: typing.Optional[socket.socket] = None,
        gss_auth: bool = False,
        gss_kex: bool = False,
        gss_deleg_cred: bool = True,
        gss_host: typing.Optional[str] = None,
        gss_trust_dns: bool = True,
        banner_timeout: typing.Optional[float] = None,
        auth_timeout: typing.Optional[float] = None,
    ) -> None: ...
    def get_transport(self) -> Transport: ...
