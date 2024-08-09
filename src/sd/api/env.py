import os

import typer
from sd.utils import cmd, fmt, path

app = typer.Typer()
JSON_FILE = "sdenv.json"


def get_cache_dir():
    xdg_cache_dir = os.getenv("XDG_CACHE_HOME")
    return xdg_cache_dir if xdg_cache_dir else os.path.expanduser("~/.cache")


@app.command(help="save environment var on file!")
def save(file: str = typer.Argument(JSON_FILE, help="save file")):
    par_dir = path.get_parent(file)
    if not par_dir.is_absolute():
        file = os.path.join(get_cache_dir(), file)
    SHELL = os.getenv("SHELL")
    proc = cmd.getout(
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
    fmt.info(f"Save the current environment variables to file {file}")
    path.json_write(file, source_env)


# see @https://github.com/tiangolo/typer/issues/18
@app.callback(invoke_without_command=True)
def default(ctx: typer.Context) -> None:
    """Sub-command that I would like to be the default."""
    if ctx.invoked_subcommand is not None:
        # print("Skipping default command to run sub-command.")
        return
    save(JSON_FILE)
