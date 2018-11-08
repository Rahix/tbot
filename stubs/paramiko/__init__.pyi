import typing
import socket
from . import client

class Channel:
    def exec_command(self, command: str) -> None: ...
    def recv(self, nbytes: int) -> bytes: ...
    def recv_ready(self) -> bool: ...
    def recv_exit_status(self) -> int: ...
    def get_pty(
        self,
        term: str,
        width: typing.Optional[int] = None,
        height: typing.Optional[int] = None,
        width_pixels: typing.Optional[int] = None,
        height_pixels: typing.Optional[int] = None,
    ) -> None: ...
    def resize_pty(
        self,
        width: int,
        height: int,
        width_pixels: int,
        height_pixels: int,
    ) -> None: ...
    def invoke_shell(self) -> None: ...
    def send(self, s: typing.Union[str, bytes]) -> int: ...
    def close(self) -> None: ...
    def settimeout(self, t: typing.Optional[float]) -> None: ...
    def fileno(self) -> int: ...
    def exit_status_ready(self) -> bool: ...


class Transport:
    def open_session(
        self,
        window_size: typing.Optional[int] = None,
        max_packet_size: typing.Optional[int] = None,
        timeout: typing.Optional[float] = None,
    ) -> Channel: ...


class SSHClient:
    def load_system_host_keys(self) -> None: ...
    def set_missing_host_key_policy(self, policy: client.MissingHostKeyPolicy) -> None: ...
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
    def close(self) -> None: ...
