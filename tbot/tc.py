""" Dummies for pylint to shut up """
import pathlib

class GitRepository(pathlib.PurePosixPath):
    """ Dummy for pylint to shut up """
    pass

class UBootRepository(pathlib.PurePosixPath):
    """ Dummy for pylint to shut up """
    pass

class UnknownToolchainException(Exception):
    """ Dummy for pylint to shut up """
    pass

class Toolchain(str):
    """ Dummy for pylint to shut up """
    pass

class TftpDirectory(pathlib.PurePosixPath):
    """ Dummy for pylint to shut up """
    pass
