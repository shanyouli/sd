import os
from pathlib import Path
from typing import List, Union
from subprocess import SubprocessError
import typer
from sd.utils import cmd, fmt, path
from sd.utils.fmt import term_fmt_by_dict

app = typer.Typer()

APP_PATH = [
    "/Applications",
    os.path.expanduser("~/Applications"),
    "/System/Applications",
]
PathLink = Union[str, bytes, Path]


def get_app_list_by_path(p: PathLink) -> dict[str, str]:
    """获取目录下所有的App文件"""
    app_list = {}
    for i in os.listdir(p):
        app_path = os.path.join(p, i)
        if path.suffix_is(app_path, "app"):
            link_path = path.readlink(app_path)
            if link_path.as_posix().startswith("."):
                old_cwd = os.getcwd()
                os.chdir(Path(app_path).parent)
                app_list[link_path.name] = link_path.absolute().as_posix()
                os.chdir(old_cwd)
            else:
                app_list[link_path.name] = link_path.absolute().as_posix()
        else:
            if os.path.isdir(app_path):
                for k, v in get_app_list_by_path(app_path).items():
                    app_list[k] = v
    return app_list


def get_app_list_by_list(paths: List[PathLink]) -> dict[str, str]:
    app_lists = [get_app_list_by_path(i) for i in paths if path.is_dir(i)]
    return {k: v for i in app_lists for k, v in i.items()}


def get_app_bundleid_by_appname(app_name: str) -> str:
    "获取app的Bundle ID"
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
    bundleid = cmd.getout(f"mdls -name kMDItemCFBundleIdentifier -r '{p}'")
    if (
        bundleid == "(null)"
        and cmd.run(f"file {p} | grep 'MacOS Alias file' >/dev/null").returncode == 0
    ):
        try:
            from sd.api.macos import alias

            p = alias(p, None)
            # mdls -name 不支持 /nix/store/ 下文件
            if not p.startswith("/nix/store"):
                bundleid = cmd.getout(f"mdls -name kMDItemCFBundleIdentifier -r '{p}'")
        except (ModuleNotFoundError, SubprocessError) as e:
            bundleid = "(null)"
            fmt.error(e)
    if bundleid == "(null)":
        bundleid = get_app_bundleid_by_info(p)
        if bundleid:
            return bundleid
        else:
            try:
                return get_app_bundleid_by_appname(Path(p).name)
            except SubprocessError as e:
                fmt.info(f"The path of {p} has no bundleid! {str(e)}")
                return "null"
    else:
        return bundleid


@app.command(help="Get All App Name")
def display():
    app_lists = get_app_list_by_list(APP_PATH)
    term_fmt_by_dict(dict(sorted(app_lists.items(), key=lambda x: x[0])))


@app.command(help="Display all app BundleId")
def db():
    app_lists = get_app_list_by_list(APP_PATH)
    app_dict = {i: get_app_bundleid_by_path(app_lists[i]) for i in app_lists}
    term_fmt_by_dict(dict(sorted(app_dict.items(), key=lambda x: x[0])))


@app.command(help="get one app bundleid")
def get(
    pkg: str = typer.Argument(
        None, help="App Path, Please run: getBundleId.py display"
    ),
):
    bundleid = None
    if path.is_exist(pkg):
        p = path.abspath(pkg)
        bundleid = get_app_bundleid_by_path(p)
    else:
        app_lists = get_app_list_by_list(APP_PATH)
        if pkg in app_lists.keys():
            bundleid = get_app_bundleid_by_path(app_lists[pkg])
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
