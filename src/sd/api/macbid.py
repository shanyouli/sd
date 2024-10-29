import os
from pathlib import Path
from typing import List, Union
from subprocess import SubprocessError
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


def get_app_bundleid_by_appname(app_name: str) -> str:
    "获取app的Bundle Ip"
    return cmd.getout(f"osascript -e 'id of app \"{app_name}\"'")


def get_app_bundleid_by_info(f: PathLink) -> str:
    p = os.path.join(f, "Contents", "Info.plist")
    if path.is_exist(p):
        try:
            import plistlib

            pl = plistlib.loads(Path(p).read_bytes())
            return pl.get("CFBundleIdentifier")
        except ModuleNotFoundError as e:
            fmt.error(e)


def get_app_bundleid_by_path(p: PathLink) -> str:
    "获取 路径的 bundle ip， 该路径必须是app程序"
    bundleid = cmd.getout(f"mdls -name kMDItemCFBundleIdentifier -r {p}")
    if bundleid == "(null)":
        if cmd.run(f"file {p} | grep 'MacOS Alias file' >/dev/null").returncode == 0:
            try:
                from sd.api.macos import alias

                p = alias(p, None)
            except ModuleNotFoundError as e:
                fmt.error(e)
        try:
            bundleid = cmd.getout(f"mdls -name kMDItemCFBundleIdentifier -r {p}")
        except SubprocessError as e:
            bundleid = (
                get_app_bundleid_by_info(p) if "could not find" in str(e) else "(null)"
            )
    if bundleid == "(null)":
        fmt.info(f"The path of {p} has no bundleid!")
        return "null"
    else:
        return bundleid


@app.command(help="Get All App Name")
def display():
    app_lists = get_app_list_by_list(app_path)
    term_fmt_by_list(app_lists)


@app.command(help="Display all app BundleId")
def db():
    app_lists = get_app_list_by_list(app_path)
    app_dict = {i: get_app_bundleid_by_appname(i) for i in app_lists}
    term_fmt_by_dict(app_dict)


@app.command(help="get one app bundleid")
def get(
    pkg: str = typer.Argument(
        None, help="App Path, Please run: getBundleId.py display"
    ),
):
    bundleid = None
    if pkg in get_app_list_by_list(app_path):
        bundleid = get_app_bundleid_by_appname(pkg)
    elif path.is_exist(pkg):
        p = path.abspath(pkg)
        bundleid = get_app_bundleid_by_path(p)
    else:
        fmt.error(f"Didn't find the {pkg}, please use the command display view")
        raise typer.Abort()
    if bundleid is None or bundleid == "null":
        fmt.warn(f"No bundleid found for {pkg}, please check if {pkg} is the program")
    else:
        fmt.info(f"The bundleid of {pkg} is {bundleid}")
    return bundleid


@app.callback(invoke_without_command=True)
def default(ctx: typer.Context) -> None:
    """Sub-command that I would like to be the default."""
    if ctx.invoked_subcommand is not None:
        # print("Skipping default command to run sub-command.")
        return
    display()


if __name__ == "__main__":
    app()
