import json
import os
from pathlib import Path
from typing import List, Union
from sd.utils import cmd

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
    p = Path(os.path.expanduser(p))
    return p.resolve() if p.is_symlink() else p


def mkdir(p: PathLink) -> None:
    p = Path(os.path.expanduser(p))
    if p.exists():
        if not p.is_dir():
            raise FileExistsError(f"Path {p._str} already exists")
    else:
        try:
            os.makedirs()
        except PermissionError:
            cmd.run(f"sudo mkdir -p {os.path.abspath(p)}")


def json_write(p: PathLink, dic, indent: int = 2) -> None:
    parent_dir = get_parent(p)
    mkdir(parent_dir)
    with open(p, mode="w", encoding="utf-8") as f:
        # json.dump(source_env, f, indent=2)
        f.write(json.dumps(dic, indent=indent))


def json_read(p: PathLink) -> dict:
    p = Path(os.path.expanduser(p))
    if is_file(p):
        with open(p, mode="r", encoding="utf-8") as f:
            return json.load(f)
