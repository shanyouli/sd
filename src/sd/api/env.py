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
    SHELL = SHELL if SHELL.startswith("/") else cmd.getout(f"which {SHELL}")
    proc = cmd.getout(
        f"""
    unset PATH __NIX_DARWIN_SET_ENVIRONMENT_DONE __ETC_ZPROFILE_SOURCED
    unset __ETC_ZSHENV_SOURCED __ETC_ZSHRC_SOURCED __HM_SESS_VARS_SOURCED
    unset FZF_DEFAULT_OPTS
    {SHELL} -i -c -l "env"
    """
    )
    # 使用正则表达式去除转义字符
    source_env = {}
    prev_key = None
    for tup in proc.split("\n"):
        if tup.find("=") != -1:
            temp = tup.split("=")
            prev_key = temp[0].strip()
            if prev_key.endswith("\\SHELL"):
                prev_key = None
            elif prev_key == "PATH":
                temp_values = [
                    i
                    for i in temp[1].strip().split(":")
                    if not i.startswith("/nix/store")
                ]
                source_env["PATH"] = ":".join(temp_values)
            elif prev_key not in [
                "__NIX_DARWIN_SET_ENVIRONMENT_DONE",
                "__ETC_ZPROFILE_SOURCED",
                "__ETC_ZSHENV_SOURCED",
                "__ETC_ZSHRC_SOURCED",
                "__HM_SESS_VARS_SOURCED",
            ]:
                source_env[prev_key] = (
                    temp[1].strip() if len(temp) == 2 else "=".join(temp[1:])
                )
            else:
                prev_key = None
        elif prev_key is not None:
            source_env[prev_key] = (
                "" if source_env[prev_key] == "" else (source_env[prev_key] + "\n")
            ) + tup.strip()
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
