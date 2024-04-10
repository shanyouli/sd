import os
from pathlib import Path
from typing import List, Union

import typer
from sd.utils.cmd import cmd_getout
from sd.utils.enums import Colors
from sd.utils.fmt import term_fmt_by_dict, term_fmt_by_list

app = typer.Typer()

app_path = ["/Applications", os.path.expanduser("~/Applications")]
PathLink = Union[str, bytes, Path]


def get_app_list_by_path(path: PathLink) -> List[str]:
    """获取目录下所有的App文件"""
    app_list = []
    for i in os.listdir(path):
        if i.endswith(".app"):
            i_path = Path(os.path.join(path, i))
            app_list.append(
                i_path.resolve().name if i_path.is_symlink() else i_path.name
            )
        else:
            subpath = os.path.join(path, i)
            if os.path.isdir(subpath):
                for j in get_app_list_by_path(subpath):
                    app_list.append(j)
    return list(set(app_list))


def get_app_list_by_list(paths: List[PathLink]) -> List[str]:
    app_lists = [get_app_list_by_path(i) for i in paths]
    return [j for i in app_lists for j in i]


def get_app_bundleid(app_name: str) -> str:
    "获取app的Bundle Ip"
    return cmd_getout(f"osascript -e 'id of app \"{app_name}\"'")


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
    if os.path.exists(pkg) or pkg in get_app_list_by_list(app_path):
        typer.secho(get_app_bundleid(pkg), fg=Colors.INFO.value)
    else:
        typer.secho(
            f"Didn't find the {pkg}, please use the command display view",
            fg=Colors.ERROR.value,
        )
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
