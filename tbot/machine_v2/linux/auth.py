import typing
import pathlib
from .. import linux


class AuthenticatorBase:
    pass


class PasswordAuthenticator(AuthenticatorBase):
    __slots__ = ("password",)

    def __init__(self, password: str) -> None:
        self.password = password


class PrivateKeyAuthenticator(AuthenticatorBase):
    __slots__ = ("key_file",)

    def __init__(
        self, key_file: typing.Union[str, linux.Path, pathlib.PurePath]
    ) -> None:
        self.key_file = key_file

    def get_key_for_host(self, host: typing.Optional[linux.LinuxShell]) -> str:
        if isinstance(self.key_file, str):
            return self.key_file
        elif isinstance(self.key_file, pathlib.PurePath):
            return str(self.key_file)
        elif isinstance(self.key_file, linux.Path):
            if host is not None:
                assert (
                    self.key_file.host is host
                ), f"Private key is associated with wrong host"
            return self.key_file._local_str()


class NoneAuthenticator(AuthenticatorBase):
    pass


class UndefinedAuthenticator(AuthenticatorBase):
    # Python has no real union types which could be used to ensure all variants
    # are checked in code.  As a workaround, the else-branch should access this
    # _undefined_marker property like this:
    #
    #     else:
    #         if typing.TYPE_CHECKING:
    #             authenticator._undefined_marker
    #         raise ValueError(f"Unknown authenticator {authenticator!r}")
    #
    # mypy will then raise an error if any variants were not checked in
    # elif-blocks beforehand.
    _undefined_marker = None


Authenticator = typing.Union[
    PasswordAuthenticator,
    PrivateKeyAuthenticator,
    NoneAuthenticator,
    UndefinedAuthenticator,
]
