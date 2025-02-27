import os
from typing import List

import typer
from sd.utils.enums import Colors


def str_len(s) -> int:
    try:
        import wcwidth

        return wcwidth.wcswidth(s)
    except ModuleNotFoundError:
        return len(s)


def str_rjust(text, length, padding=" "):
    return padding * max(0, length - str_len(text)) + text


def str_ljust(text, length, padding=" "):
    return text + padding * max(0, length - str_len(text))


def columns() -> int:
    """获取当前终端的列数"""
    cols = os.get_terminal_size().columns
    if cols == 0:
        cols = 80
    return cols


def max_size(lst: List[str]) -> int:
    return max(str_len(i) for i in lst)


def term_fmt_by_list(lst: List[str], space: int = 4, use_num: bool = True):
    """
    lst -> List
    space -> 空格
    sep -> 标记分割符
    """
    pre_size = str_len(str(len(lst))) if use_num else 0
    term_columns = columns()
    ceil_size = max_size(lst)
    sep_str = ": " if use_num else ""
    sep_len = str_len(sep_str)
    ceil_size_and_sep = pre_size + sep_len + ceil_size
    num = term_columns // ceil_size_and_sep
    if num == 0:
        num = 1
    elif (num - 1) * space + num * ceil_size_and_sep > term_columns:
        num -= 1
    messages = ""
    split = " " * space
    for i, ceil_msg in enumerate(lst):
        numstr = (
            typer.style(str_rjust(f"{i + 1}", pre_size, "0"), fg=Colors.INFO.value)
            if use_num
            else ""
        )
        if (i + 1) % num == 0:
            ceil_msg = typer.style(ceil_msg, fg=Colors.INFO.value)
            messages += f"{numstr}{sep_str}{ceil_msg}"
            typer.echo(messages)
            messages = ""
        else:
            ceil_msg = typer.style(str_ljust(ceil_msg, ceil_size), fg=Colors.INFO.value)
            messages += f"{numstr}{sep_str}{ceil_msg}{split}"


def term_fmt_by_dict(
    dic: dict[str, str], space: int = 4, dic_sep: str = "   ", use_num: bool = True
) -> None:
    pre_keys = dic.keys()
    pre_vals = [str(i) for i in dic.values()]
    pre_size = str_len(str(len(pre_keys))) if use_num else 0
    term_columns = columns()
    keys_size = max_size(pre_keys)
    vals_size = max_size(pre_vals)
    split = " " * space
    sep_str = ": " if use_num else ""
    sep_len = str_len(sep_str) if use_num else 0
    dic_sep_len = str_len(dic_sep)
    ceil_len = keys_size + vals_size + sep_len + dic_sep_len + pre_size
    num = term_columns // ceil_len
    if num == 0:
        num = 1
    elif (num - 1) * space + num * ceil_len > term_columns:
        num -= 1
    messages = ""
    for i, key_msg in enumerate(pre_keys):
        numstr = (
            typer.style(str_rjust(f"{i + 1}", pre_size, "0"), fg=Colors.INFO.value)
            if use_num
            else ""
        )
        ceil_msg = typer.style(str_ljust(key_msg, keys_size), fg=Colors.INFO.value)
        dic_msg = typer.style(dic_sep, fg=Colors.WARN.value)
        if (i + 1) % num == 0:
            val_msg = typer.style(str(dic[key_msg]), fg=Colors.INFO.value)
            messages += f"{numstr}{sep_str}{ceil_msg}{dic_msg}{val_msg}"
            typer.echo(messages)
            messages = ""
        else:
            val_msg = typer.style(
                str_ljust(str(dic[key_msg]), vals_size), fg=Colors.INFO.value
            )
            messages += f"{numstr}{sep_str}{ceil_msg}{dic_msg}{val_msg}{split}"


def info(msg: str) -> None:
    typer.secho(f"INFO: {msg}", fg=Colors.INFO.value)


def echo(msg: str) -> None:
    typer.echo(f"{msg}")


def warn(msg: str) -> None:
    typer.secho(f"WARN: {msg}", fg=Colors.WARN.value)


def error(msg: str) -> None:
    typer.secho(f"ERROR: {msg}", fg=Colors.ERROR.value)


def success(msg: str) -> None:
    typer.secho(f"SUCCESS: {msg}", fg=Colors.SUCCESS.value)
