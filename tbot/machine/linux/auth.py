import abc
import pathlib


class Authenticator(abc.ABC):
    """Authenticate a connection to a linux host."""

    pass


class PasswordAuthenticator(Authenticator):
    """Authenticate using a password."""

    def __init__(self, password: str) -> None:
        """
        Initialize this authenticator with a given password.

        :param str password: The password that will be used
                             with this authenticator.
        """
        self.password = password
        self.key = None


class PrivateKeyAuthenticator(Authenticator):
    """Authenticate using a private key."""

    def __init__(self, key: pathlib.PurePath) -> None:
        """
        Initialize this authenticator with a path to a private key.

        :param pathlib.Path key: Path to the private key file
        """
        self.password = None
        self.key = key
