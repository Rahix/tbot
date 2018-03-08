import pathlib

class GitRepository(pathlib.PurePosixPath):
    pass

class UBootRepository(pathlib.PurePosixPath):
    pass

class UnknownToolchainException(Exception):
    pass

class Toolchain(str):
    pass
