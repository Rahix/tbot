import typing


class Shell:
    """
    Generic sh shell.

    :cvar str name: Name of this shell (Also used when creating a new instance of
        this shell.)
    """

    name = "sh"

    @staticmethod
    def set_prompt(prompt: str) -> str:
        """
        Set the prompt of this shell to ``prompt``.

        :param str prompt: The new ``PS1``
        :rtype: str
        :returns: The command to set the prompt in this shell.
        """
        return f"PS1='{prompt}'"

    @staticmethod
    def set_prompt2(prompt: str) -> typing.Optional[str]:
        """
        Set the secondary prompt of this shell to ``prompt``.

        :param str prompt: The new ``PS2``
        :rtype: str, None
        :returns: The command to set PS2 in this shell if it exists.
        """
        return f"PS2='{prompt}'"

    @staticmethod
    def disable_editing() -> typing.Optional[str]:
        """
        Disable readline or equivalents in this shell.

        :rtype: str, None
        :returns: The command to disable line editing in this shell if it exists.
        """
        return "stty cols 1024"

    @staticmethod
    def enable_editing() -> typing.Optional[str]:
        """
        Enable readline or equivalents in this shell.

        :rtype: str, None
        :returns: The command to enable line editing in this shell if it exists.
        """
        pass

    @staticmethod
    def disable_history() -> typing.Optional[str]:
        """
        Disable writing to the history file.

        :rtype: str, None
        :returns: The command to disable history in this shell if it exists.
        """
        pass
