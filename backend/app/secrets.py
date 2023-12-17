import logging
import os
from pathlib import Path
from typing import Any, Iterator, Mapping

import toml

from .lazy import lazy
from .map import Map

SECRET_FILE_PATH = Path(os.environ["SECRET_FILE_PATH"], "secrets.toml")


def load_toml() -> Map:
    if SECRET_FILE_PATH.exists():
        logging.info("Loading secrets from TOML file.")
        return Map(toml.load(SECRET_FILE_PATH))
    return Map({})


class Secrets(Mapping[str, Any]):
    instance = lazy(load_toml)

    def __getattr__(self, key: str) -> Any:
        return getattr(Secrets.instance(), key)

    def __getitem__(self, key: str) -> Any:
        return Secrets.instance()[key]

    def __iter__(self) -> Iterator[str]:
        return iter(Secrets.instance())

    def __len__(self) -> int:
        return len(Secrets.instance())

    def __repr__(self) -> str:
        return repr(self.instance())


secrets = Secrets()
