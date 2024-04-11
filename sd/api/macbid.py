import os
from pathlib import Path
from typing import List, Union

import typer
from sd.utils import cmd, fmt, path
from sd.utils.fmt import term_fmt_by_dict, term_fmt_by_list

app = typer.Typer()

app_path = ["/Applications", os.path.expanduser("~/Applications")]
PathLink = Union[str, bytes, Path]


def get_app_list_by_path(p: PathLink) -> List[str]:
    """获取目录下所有的App文件"""
    app_list = []
    for i in os.listdir(p):
        app_path = os.path.join(p, i)
        if path.suffix_is(app_path, "app"):
            app_list.append(path.readlink(app_path).name)
        else:
            if os.path.isdir(app_path):
                for j in get_app_list_by_path(app_path):
                    app_list.append(j)
    return list(set(app_list))


def get_app_list_by_list(paths: List[PathLink]) -> List[str]:
    app_lists = [get_app_list_by_path(i) for i in paths if path.is_dir(i)]
    return [j for i in app_lists for j in i]


def get_app_bundleid(app_name: str) -> str:
    "获取app的Bundle Ip"
    return cmd.getout(f"osascript -e 'id of app \"{app_name}\"'")


@app.command(help="Get All App Name")
def display():
    app_lists = get_app_list_by_list(app_path)
    term_fmt_by_list(app_lists)


@app.command(help="Display all app BundleId")
def db():
    app_lists = get_app_list_by_list(app_path)
    app_dict = {i: get_app_bundleid(i) for i in app_lists}
    term_fmt_by_dict(app_dict)


@app.command(help="get one app bundleid")
def get(
    pkg: str = typer.Argument(None, help="App Path, Please run: getBundleId.py display")
):
    if path.is_exist(pkg) or pkg in get_app_list_by_list(app_path):
        fmt.info(get_app_bundleid(pkg))
    else:
        fmt.error(f"Didn't find the {pkg}, please use the command display view")
        raise typer.Abort()


@app.callback(invoke_without_command=True)
def default(ctx: typer.Context) -> None:
    """Sub-command that I would like to be the default."""
    if ctx.invoked_subcommand is not None:
        # print("Skipping default command to run sub-command.")
        return
    display()


if __name__ == "__main__":
    app()
