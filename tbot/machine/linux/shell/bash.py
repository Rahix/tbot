import typing
from tbot.machine.linux import shell


class Bash(shell.Shell):
    """Bourne-Again SHell."""

    name = "bash"

    @staticmethod
    def set_prompt(prompt: str) -> str:  # noqa: D102
        return f"PROMPT_COMMAND=''\nPS1='{prompt}'"

    @staticmethod
    def disable_editing() -> typing.Optional[str]:  # noqa: D102
        return "set +o emacs; set +o vi"

    @staticmethod
    def enable_editing() -> typing.Optional[str]:  # noqa: D102
        return "set -o emacs"

    @staticmethod
    def disable_history() -> typing.Optional[str]:  # noqa: D102
        return "unset HISTFILE"
