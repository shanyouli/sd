import json
import os
from pathlib import Path
from typing import List, Union
from sd.utils import cmd

PathLink = Union[str, bytes, Path]


def is_exist(p: PathLink) -> bool:
    return Path(p).expanduser().exists()


def is_file(p: PathLink) -> bool:
    return Path(p).expanduser().is_file()


def is_link(p: PathLink) -> bool:
    return Path(p).expanduser().is_symlink()


def is_dir(p: PathLink) -> bool:
    return Path(p).expanduser().is_dir()


def get_parent(p: PathLink) -> Path:
    return Path(p).expanduser().parent


def suffix_is(p: PathLink, ext) -> bool:
    ext = ext if ext.startswith(".") else f".{ext}"
    return Path(p).expanduser().suffix == ext


def readlink(p: PathLink, isLast: bool = False) -> Path:
    p = Path(p).expanduser()
    if p.is_symlink():
        return p.resolve() if isLast else p.readlink()
    else:
        return p

def link_exists(p: PathLink) -> bool:
    p = readlink(p)
    return p.exists()

def mkdir(p: PathLink) -> None:
    p = Path(p).expanduser()
    if p.exists():
        if not p.is_dir():
            raise FileExistsError(f"Path {p._str} already exists")
    else:
        try:
            os.makedirs()
        except PermissionError:
            cmd.getout(f"sudo mkdir -p {os.path.abspath(p)}")

def remove_file_or_link(p: PathLink) -> None:
    try:
        if is_link(p):
            Path(p).unlink()
        elif is_file(p):
            os.remove(p)
    except PermissionError:
        cmd.getout(f"sudo rm -vf {os.path.abspath(p)}")

def json_write(p: PathLink, dic, indent: int = 2) -> None:
    parent_dir = get_parent(p)
    mkdir(parent_dir)
    with open(p, mode="w", encoding="utf-8") as f:
        # json.dump(source_env, f, indent=2)
        f.write(json.dumps(dic, indent=indent))


def json_read(p: PathLink) -> dict:
    p = Path(p).expanduser()
    if is_file(p):
        with open(p, mode="r", encoding="utf-8") as f:
            return json.load(f)
