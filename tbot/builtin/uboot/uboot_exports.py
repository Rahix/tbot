"""
Exports for U-Boot
------------------
"""
from tbot import tc

EXPORT = ["UBootRepository"]

class UBootRepository(tc.GitRepository):
    """
    A meta object to represent a checked out version of U-Boot.
    Can be created with :func:`uboot_checkout` or :func:`uboot_checkout_and_build`
    """
    pass
