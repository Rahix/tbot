import typing
import abc


class Shell(abc.ABC):
    name = "sh"

    @staticmethod
    def set_prompt(prompt: str) -> str:
        return f"PS1='{prompt}'"

    @staticmethod
    def set_prompt2(prompt: str) -> typing.Optional[str]:
        return f"PS2='{prompt}'"

    @staticmethod
    def disable_editing() -> typing.Optional[str]:
        return "stty cols 1024"

    @staticmethod
    def enable_editing() -> typing.Optional[str]:
        pass

    @staticmethod
    def disable_history() -> typing.Optional[str]:
        pass
