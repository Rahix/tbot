"""
Exports for toolchains
----------------------
"""

EXPORT = ["Toolchain", "UnknownToolchainException"]

class UnknownToolchainException(Exception):
    """ The toolchain provided was not found in the config """
    pass

class Toolchain(str):
    """
    A meta object to represent a toolchain.
    Can be created with :func:`~tbot.builtin.toolchain.toolchain_get`
    """
    pass
