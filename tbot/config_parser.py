"""
Config parser
-------------
"""
import random
import typing
import toml


def apply_config(acc: typing.Dict[str, typing.Any],
                 cur: typing.Dict[str, typing.Any]) -> typing.Dict[str, typing.Any]:
    """ Add keys from one config object to another """
    if isinstance(cur, dict):
        for k in cur:
            if k in acc:
                acc[k] = apply_config(acc[k], cur[k])
            else:
                acc[k] = cur[k]
    elif isinstance(cur, list):
        for i, value in enumerate(cur):
            acc[i] = apply_config(acc[i], value)
    else:
        acc = cur
    return acc


class Config:
    """ Configuration container """
    def __init__(self, configs: typing.List[str]) -> None:
        configs_parsed = [toml.load(config) for config in configs]

        merged: typing.Dict[str, typing.Any] = dict()
        for config in configs_parsed:
            merged = apply_config(merged, config)

        self.cfg = merged

        # Set a few commonly used config options directly
        self.lab_name = self.get("lab.name", "defaultLabName")
        self.board_name = self.get("board.name", "defaultBoardName")
        use_rand = self.get("tbot.random_workdir", False)
        self.workdir = self.get("tbot.workdir", "/tmp/tbot-{board}-{rand}") \
            .format(rand=str(random.randint(1111, 999999999)) \
                        if use_rand else "NORAND",
                    board=self.board_name,
                    lab=self.lab_name)

    def try_get(self, key: str) -> typing.Any:
        """
        Try accessing a config key

        :param key: The key to be retrieved
        :returns: The value associated with the key or None if the key was not found
        """
        try:
            key_path = key.split(".")
            current = self.cfg
            for key_segment in key_path:
                current = current[key_segment]
            return current
        except KeyError:
            return None

    def get(self, key: str, default: typing.Any = None) -> typing.Any:
        """
        Get a config key or return a default value

        :param key: The key to be retrieved
        :param default: The default value
        :returns: The value associated with the key or default if the key was not
            found. If default is None, this will raise an exception.
        """
        ret = self.try_get(key)
        if ret is None:
            if default is None:
                raise Exception(f"Configuration is missing \"{key}\"!")

            ret = default

        return ret
