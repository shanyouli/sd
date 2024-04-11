import os
from pathlib import Path
from typing import List, Union

PathLink = Union[str, bytes, Path]


def is_exist(p: PathLink) -> bool:
    return Path(os.path.expanduser(p)).exists()


def is_file(p: PathLink) -> bool:
    return Path(os.path.expanduser(p)).is_file()


def is_link(p: PathLink) -> bool:
    return Path(os.path.expanduser(p)).is_symlink()


def is_dir(p: PathLink) -> bool:
    return Path(os.path.expanduser(p)).is_dir()


def get_parent(p: PathLink) -> Path:
    return Path(os.path.expanduser(p)).parent


def suffix_is(p: PathLink, ext) -> bool:
    ext = ext if ext.startswith(".") else f".{ext}"
    return Path(os.path.expanduser(p)).suffix == ext


def readlink(p: PathLink) -> Path:
    p = Path(p)
    return p.resolve() if p.is_symlink() else p
