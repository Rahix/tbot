import pytest
import tbot
import testmachines


@tbot.testcase
def tc_context_simple_usage(ctx: tbot.Context, new: str) -> str:
    with ctx.request(tbot.role.LabHost) as lh:
        value = lh.env("TBOT_CTX_TESTS")
        lh.env("TBOT_CTX_TESTS", new)
        return value


@tbot.testcase
def tc_context_exclusive_usage(ctx: tbot.Context, new: str) -> str:
    with ctx.request(tbot.role.LabHost, exclusive=True) as lh:
        value = lh.env("TBOT_CTX_TESTS")
        lh.env("TBOT_CTX_TESTS", new)

        with pytest.raises(Exception, match=".*not available.*"):
            with ctx.request(tbot.role.LabHost):
                pass

        return value


@tbot.testcase
def tc_context_resetting_usage(ctx: tbot.Context, new: str) -> None:
    with ctx.request(tbot.role.LabHost, reset=True) as lh:
        value = lh.env("TBOT_CTX_TESTS")
        assert value == ""
        lh.env("TBOT_CTX_TESTS", new)


def test_simple_context() -> None:
    """
    Simply attempt requesting an instance two times without any interaction.
    """
    ctx = tbot.Context()
    testmachines.register_machines(ctx)
    with ctx:
        assert tc_context_simple_usage(ctx, "first") == ""
        assert tc_context_simple_usage(ctx, "second") == ""


def test_nested_context() -> None:
    """
    In a nested scenario, the instance should be kept alive and reused for
    later requests.
    """
    ctx = tbot.Context()
    testmachines.register_machines(ctx)
    with ctx:
        with ctx.request(tbot.role.LabHost) as outer:
            assert tc_context_simple_usage(ctx, "first") == ""
            assert outer.env("TBOT_CTX_TESTS") == "first"
            assert tc_context_simple_usage(ctx, "second") == "first"
            assert outer.env("TBOT_CTX_TESTS") == "second"
            assert tc_context_simple_usage(ctx, "third") == "second"


def test_keep_alive_context() -> None:
    """
    A keep-alive context should behave as if it was nested for all instances.
    """
    ctx = tbot.Context(keep_alive=True)
    testmachines.register_machines(ctx)
    with ctx:
        assert tc_context_simple_usage(ctx, "first") == ""
        assert tc_context_simple_usage(ctx, "second") == "first"
        assert tc_context_simple_usage(ctx, "third") == "second"


def test_illegal_keep_alive_context() -> None:
    """
    A keep-alive context **must** have its own context-manager active.
    """
    ctx = tbot.Context(keep_alive=True)
    with pytest.raises(tbot.error.TbotException):
        with ctx.request(tbot.role.LabHost):
            pass


def test_exclusive_context() -> None:
    """
    An exclusive instance cannot be re-requested and is torn down on context exit.
    """
    ctx = tbot.Context()
    testmachines.register_machines(ctx)
    with ctx:
        with ctx.request(tbot.role.LabHost) as outer:
            assert tc_context_simple_usage(ctx, "first") == ""
            outer.exec0("true")
            assert tc_context_exclusive_usage(ctx, "second") == "first"
            with pytest.raises(tbot.machine.channel.ChannelClosedException):
                outer.exec0("true")
            assert tc_context_simple_usage(ctx, "third") == ""


def test_resetting_context() -> None:
    """
    An request(reset=True) should always get a pristine instance.
    """
    ctx = tbot.Context()
    testmachines.register_machines(ctx)
    with ctx:
        with ctx.request(tbot.role.LabHost) as outer:
            assert tc_context_simple_usage(ctx, "first") == ""
            outer.exec0("true")
            tc_context_resetting_usage(ctx, "second")
            with pytest.raises(tbot.machine.channel.ChannelClosedException):
                outer.exec0("true")
            assert tc_context_simple_usage(ctx, "third") == "second"
            tc_context_resetting_usage(ctx, "fourth")


def test_keep_alive_exclusive_context() -> None:
    """
    Test invariants of exclusive access for a keep-alive context.
    """
    ctx = tbot.Context(keep_alive=True)
    testmachines.register_machines(ctx)
    with ctx:
        assert tc_context_simple_usage(ctx, "first") == ""
        assert tc_context_exclusive_usage(ctx, "second") == "first"
        assert tc_context_simple_usage(ctx, "third") == ""


def test_keep_alive_resetting_context() -> None:
    """
    Test invariants of resetting access for a keep-alive context.
    """
    ctx = tbot.Context(keep_alive=True)
    testmachines.register_machines(ctx)
    with ctx:
        assert tc_context_simple_usage(ctx, "first") == ""
        tc_context_resetting_usage(ctx, "second")
        assert tc_context_simple_usage(ctx, "third") == "second"
        tc_context_resetting_usage(ctx, "fourth")


def test_reset_on_error_context() -> None:
    """
    Make sure the reset_on_error mode works as intended.
    """
    ctx = tbot.Context()
    testmachines.register_machines(ctx)
    with ctx:
        with ctx.request(tbot.role.LabHost) as outer:
            with pytest.raises(Exception):
                with ctx.request(tbot.role.LabHost, reset_on_error=True) as inner1:
                    inner1.env("TBOT_CTX_TESTS", "inner1")
                    raise Exception()

            with ctx.request(tbot.role.LabHost) as inner2:
                assert inner2.env("TBOT_CTX_TESTS") != "inner1"

            with pytest.raises(tbot.machine.channel.ChannelClosedException):
                outer.exec0("true")


def test_keep_alive_reset_on_error_context() -> None:
    """
    Make sure the reset_on_error mode works as intended, when keep_alive is enabled.
    """
    ctx = tbot.Context(keep_alive=True)
    testmachines.register_machines(ctx)
    with ctx:
        with pytest.raises(Exception):
            with ctx.request(tbot.role.LabHost, reset_on_error=True) as inner1:
                inner1.env("TBOT_CTX_TESTS", "inner1")
                raise Exception()

        with ctx.request(tbot.role.LabHost) as inner2:
            assert inner2.env("TBOT_CTX_TESTS") != "inner1"


def test_reset_on_error_by_default_context() -> None:
    """
    Make sure the reset_on_error mode works as intended, when keep_alive is enabled.
    """
    ctx = tbot.Context(keep_alive=True, reset_on_error_by_default=True)
    testmachines.register_machines(ctx)
    with ctx:
        with pytest.raises(Exception):
            with ctx.request(tbot.role.LabHost) as inner1:
                inner1.env("TBOT_CTX_TESTS", "inner1")
                raise Exception()

        with ctx.request(tbot.role.LabHost) as inner2:
            assert inner2.env("TBOT_CTX_TESTS") != "inner1"
