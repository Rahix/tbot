import random
from tbot.config import Config

# TODO: Remove old tomls
def config(cfg: Config) -> Config:
    rand = random.randint(1000, 10000)
    cfg["tbot.workdir"] = f"/tmp/tbot-{rand}"
