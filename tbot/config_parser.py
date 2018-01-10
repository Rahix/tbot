""" TBOT config parser """
import random
import toml


def apply_config(acc, cur):
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
    """ TBOT config """
    def __init__(self, configs):
        configs_parsed = [toml.load(config) for config in configs]

        merged = dict()
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

    def try_get(self, key):
        """ Try getting a config value. If it does not exist, return None """
        try:
            key_path = key.split(".")
            current = self.cfg
            for key_segment in key_path:
                current = current[key_segment]
            return current
        except KeyError:
            return None

    def get(self, key, default=None):
        """ Get a config value. If it does not exist, return default. If
            default is None, raise an Exception """
        ret = self.try_get(key)
        if ret is None:
            if default is None:
                raise Exception(f"Configuration is missing \"{key}\"!")

            ret = default

        return ret
