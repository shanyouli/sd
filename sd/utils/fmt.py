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


def term_fmt_by_list(lst: List[str], space: int = 4):
    """
    lst -> List
    space -> 空格
    sep -> 标记分割符
    """
    pre_size = str_len(str(len(lst)))
    term_columns = columns()
    cell_size = max_size(lst)
    sep_len = str_len(": ")
    num = term_columns // (pre_size + sep_len + space + cell_size)
    if num == 0:
        num = 1
    messages = ""
    split = " " * space
    for i, cell_msg in enumerate(lst):
        numstr=typer.style(str_rjust(f"{i + 1}", pre_size, "0"), fg=Colors.INFO.value)
        cell_msg = typer.style(str_ljust(cell_msg, cell_size), fg=Colors.INFO.value)
        messages += f"{numstr}: {cell_msg}{split}"
        if (i + 1) % num == 0:
            typer.echo(messages)
            messages = ""
