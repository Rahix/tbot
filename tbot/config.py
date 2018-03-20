"""
Configuration
-------------
"""
import typing

class ConfigAssignException(Exception):
    """ An error while writing a config value """
    pass

class Config(dict):
    """
    A TBot configuration

    Access configuaration items by using a ``.`` separated key-path, eg::

        hooks = cfg["uboot.test.hooks"]

    By default, this raises an exception if the value was not found. You can
    supply a default value that will be returned if the value was not found
    instead::

        has_venv = cfg["uboot.test.has_venv", True]

    The configuration is available as ``tb.config`` in all testcases.
    """
    def __getitem__(self, keys: typing.Union[str, typing.Tuple[str, typing.Any]]) -> typing.Any:
        if isinstance(keys, str):
            key = keys
        else:
            key = keys[0]

        try:
            key_path = key.split(".")
            cfg = self
            for key_segment in key_path[:-1]:
                try:
                    cfg = cfg.__getitem__(key_segment)
                except KeyError:
                    new_cfg = Config()
                    cfg.__setitem__(key_segment, new_cfg)
                    cfg = new_cfg
                if not isinstance(cfg, Config):
                    raise KeyError(f"{key_segment} is not a config subdir")
            return super(Config, cfg).__getitem__(key_path[-1])
        except KeyError as key_error:
            if isinstance(keys, str):
                raise key_error
            return keys[1]

    def __setitem__(self, key: str, value: typing.Any) -> None:
        if "." in key:
            key_path = key.split(".")
            cfg = self
            for key_segment in key_path[:-1]:
                try:
                    cfg = super(Config, cfg).__getitem__(key_segment)
                except KeyError:
                    new_cfg = Config()
                    super(Config, cfg).__setitem__(key_segment, new_cfg)
                    cfg = new_cfg
                if not isinstance(cfg, Config):
                    raise KeyError(f"{key_segment} is not a config subdir")
            cfg.__setitem__(key_path[-1], value)
        else:
            if isinstance(value, dict):
                try:
                    cfg = super().__getitem__(key)
                except KeyError:
                    cfg = Config()
                    super().__setitem__(key, cfg)

                if not isinstance(cfg, Config):
                    raise ConfigAssignException("Trying to overwrite a value with a subtree")

                for inner_key, inner_value in value.items():
                    cfg.__setitem__(inner_key, inner_value)
            else:
                if key in self and isinstance(super().__getitem__(key), Config):
                    # We are trying to overwrite a subdir, this should not happen
                    raise ConfigAssignException(f"Trying to overwrite a subdir: '{key}'")
                else:
                    super().__setitem__(key, value)

    def get(self, _key: str, _default: typing.Any = None) -> None:
        raise Exception("The get method has been removed, please use [indexing]")
