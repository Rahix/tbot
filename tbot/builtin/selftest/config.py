"""
TBot config selftests
---------------------
"""
import pathlib
import typing
import tempfile
import tbot

def parse_config(configs: typing.List[pathlib.Path]) -> tbot.config.Config:
    """ Wrapper around the tbot config parser for convenience """
    cfg = tbot.config.Config()
    tbot.config_parser.parse_config(cfg, configs)
    return cfg

@tbot.testcase
def selftest_config(tb: tbot.TBot) -> None:
    """ Test TBot's config framework """
    with tempfile.TemporaryDirectory() as tempdir:
        tempdir = pathlib.Path(str(tempdir))

####################################################################
        tb.log.log_debug("Testing a single config ...")
        with open(tempdir / "c1.py", mode='w') as c:
            c.write("""\
def config(cfg):
    cfg["foo"] = 1
""")

        cfg = parse_config([tempdir / "c1.py"])
        assert cfg["foo"] == 1

####################################################################
        tb.log.log_debug("Testing overwriting a single value ...")
        with open(tempdir / "c2.py", mode='w') as c:
            c.write("""\
def config(cfg):
    cfg["foo"] = 2
""")

        cfg = parse_config([tempdir / "c1.py",
                            tempdir / "c2.py",
                           ])
        assert cfg["foo"] == 2

####################################################################
        tb.log.log_debug("Testing overwriting a nested value ...")
        with open(tempdir / "c3.py", mode='w') as c:
            c.write("""\
def config(cfg):
    cfg["foo"] = {
        "bar": 3,
    }
""")

        with open(tempdir / "c4.py", mode='w') as c:
            c.write("""\
def config(cfg):
    cfg["foo.bar"] = 4
""")

        cfg = parse_config([tempdir / "c3.py",
                            tempdir / "c4.py",
                           ])
        assert cfg["foo.bar"] == 4

####################################################################
        tb.log.log_debug("Testing overwriting a value with a subtree ...")
        with open(tempdir / "c5.py", mode='w') as c:
            c.write("""\
def config(cfg):
    cfg["foo.bar"] = {
        "baz": 5,
    }
""")

        fail = False
        try:
            cfg = parse_config([tempdir / "c3.py",
                                tempdir / "c5.py",
                               ])
        except tbot.config.ConfigAssignException:
            fail = True
        assert fail is True

####################################################################
        tb.log.log_debug("Testing overwriting a subtree with a value ...")
        fail = False
        try:
            cfg = parse_config([tempdir / "c5.py",
                                tempdir / "c3.py",
                               ])
        except tbot.config.ConfigAssignException:
            fail = True
        assert fail is True

####################################################################
        tb.log.log_debug("Testing overwriting a subtree with a subtree (merge)...")
        with open(tempdir / "c6.py", mode='w') as c:
            c.write("""\
def config(cfg):
    cfg["foo.bar"] = {
        "foo": 6,
    }
""")

        cfg = parse_config([tempdir / "c5.py",
                            tempdir / "c6.py",
                           ])
        assert cfg["foo.bar.baz"] == 5
        assert cfg["foo.bar.foo"] == 6

####################################################################
        tb.log.log_debug("Testing subtree nested keys ...")
        with open(tempdir / "c7.py", mode='w') as c:
            c.write("""\
def config(cfg):
    cfg["foo"] = {
        "bar.baz": 7,
        "baz": {
            "bar": 77,
            "foo.bar": 777,
        },
    }
""")

        cfg = parse_config([tempdir / "c7.py"])
        assert cfg["foo.bar.baz"] == 7
        assert cfg["foo.baz.bar"] == 77
        assert cfg["foo.baz.foo.bar"] == 777
