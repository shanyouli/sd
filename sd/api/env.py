import json
import os

import typer
from sd.utils.cmd import cmd_getout

app = typer.Typer()
JSON_FILE = "sdenv.json"


def get_cache_dir():
    xdg_cache_dir = os.getenv("XDG_CACHE_HOME")
    if not xdg_cache_dir:
        xdg_cache_dir = os.path.expanduser("~/.cache")
    if not os.path.isdir(xdg_cache_dir):
        os.makedirs(xdg_cache_dir)
    return xdg_cache_dir


def save_env_file(f: str = JSON_FILE):
    f = os.path.expanduser(f)
    par_dir = os.path.dirname(f)
    if os.path.isabs(par_dir):
        os.makedirs(par_dir)
    elif par_dir == "":
        f = os.path.join(get_cache_dir(), f)
    SHELL = os.getenv("SHELL")
    # proc = cmd_getout(f"{SHELL} -c -i -l printenv")
    proc = cmd_getout(
        f"""
    unset PATH __NIX_DARWIN_SET_ENVIRONMENT_DONE __ETC_ZPROFILE_SOURCED
    unset __ETC_ZSHENV_SOURCED __ETC_ZSHRC_SOURC
    {SHELL} -i -c -l "printenv"
    """
    )
    proc_list = (
        i for i in proc.split("\n") if not i.startswith("_") and i.find("=") != -1
    )
    source_env = {}
    for tup in proc_list:
        if not tup.startswith("_") and tup.find("=") != -1:
            temp = tup.split("=")
            source_env[temp[0].strip()] = temp[1].strip()
    with open(f, mode="w", encoding="utf-8") as f:
        # json.dump(source_env, f, indent=2)
        f.write(json.dumps(source_env, indent=2))


@app.command(help="save environment var on file!")
def save(file: str = typer.Argument(JSON_FILE, help="save file")):
    save_env_file(file)

# see @https://github.com/tiangolo/typer/issues/18
@app.callback(invoke_without_command=True)
def default(ctx: typer.Context) -> None:
    """Sub-command that I would like to be the default."""
    if ctx.invoked_subcommand is not None:
        # print("Skipping default command to run sub-command.")
        return
    save_env_file(JSON_FILE)
