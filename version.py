import tomllib
from pathlib import Path

with Path("pyproject.toml").open("rb") as f:
    _data = tomllib.load(f)

VERSION = _data["project"]["version"]
