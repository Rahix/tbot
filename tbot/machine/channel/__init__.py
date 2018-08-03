import abc


class Channel(abc.ABC):
    @abc.abstractmethod
    def close(self) -> None:
        pass
