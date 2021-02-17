import tbot

import testmachines


def test_reentrancy(tbot_context: tbot.Context) -> None:
    """
    Check whether you can properly enter a machine context multiple times.
    """
    with tbot_context.request(testmachines.Localhost) as lo:
        with lo as h1:
            h1.env("TBOT_REENTRANCY", "foobarbaz")

        with lo as h2:
            assert h2.env("TBOT_REENTRANCY") == "foobarbaz"

        assert lo.env("TBOT_REENTRANCY") == "foobarbaz"


def test_clone_hash(tbot_context: tbot.Context) -> None:
    """
    A clone should not be the same machine but should have the same hash.
    """
    with tbot_context.request(testmachines.Localhost) as lo:
        with lo.clone() as lo2:
            assert id(lo) != id(lo2)
            assert hash(lo) == hash(lo2)
