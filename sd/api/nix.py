import os
from functools import wraps
from pathlib import Path
from subprocess import SubprocessError
from typing import List
import json
import typer
from sd.utils import cmd, fmt, path
from sd.utils.enums import (
    ISMAC,
    REMOTE_FLAKE,
    SYSTEM_ARCH,
    SYSTEM_OS,
    Dotfiles,
    FlakeOutputs,
)

DOTFILES = Dotfiles().value

app = typer.Typer()


def get_flake(current_dir: bool = False) -> str:
    if current_dir:
        try:
            check_git = cmd.getout(["git", "rev-parse", "--show-toplevel"])
            local_flake = os.path.realpath(check_git)
            return (
                local_flake
                if os.path.isfile(os.path.join(local_flake, "flake.nix"))
                else REMOTE_FLAKE
            )
        except SubprocessError:
            fmt.warn("The current directory is not a git project!")
    if DOTFILES:
        return DOTFILES
    else:
        fmt.warn("No nix configuration directory found")
        fmt.warn(
            "The configuration directory for this script can only be the following location"
        )
        fmt.warn("1.     /etc/dotfiles")
        fmt.warn("2.     /etc/nixos")
        fmt.warn("3.     ~/.nixpkgs")
        fmt.warn("4.     ~/.config/dotfiles")
        fmt.warn("5.     ~/.dotfiles")
        fmt.warn("6.     Prioritize the use of environment variables DOTFILES")
        fmt.info("Remote flake will be used")
        return REMOTE_FLAKE


def get_flake_inputs_by_lock(flake_path: Path = None):
    flake_path = os.getcwd() if flake_path is None else flake_path
    flake_lock = os.path.join(os.path.realpath(flake_path), "flake.lock")
    data_json = path.json_read(flake_lock)
    if data_json:
        try:
            return [i for i in data_json["nodes"]["root"]["inputs"].keys()]
        except KeyError as er:
            raise er
    else:
        fmt.error(f"Failed to read data from {flake_lock} file")
        raise typer.Abort()


def get_flake_inputs_by_nix(flake_path: Path = None):
    flake_path = os.getcwd() if flake_path is None else flake_path
    if path.is_file(os.path.join(os.path.realpath(flake_path), "flake.lock")):
        flake_json = cmd.getout(
            f"""nix eval --raw --impure --expr 'builtins.toJSON (builtins.getFlake "{flake_path}").inputs'"""
        )
        return [i for i in json.loads(flake_json)]
    else:
        fmt.error(f"The {flake_path} directory is not a nix-flake project")
        raise typer.Abort()


def run_cmd(cmd_list: List[str], dry_run: bool = False, shell: bool = False):
    if dry_run:
        fmt.info(cmd.fmt(cmd_list))
    else:
        cmd.run(cmd_list, shell=shell)


def get_flake_platform():
    if cmd.exists("nixos-rebuild"):
        # if we're on nixos, this command is built in
        platform = FlakeOutputs.NIXOS
    elif cmd.exists("darwin-rebuild") or ISMAC:
        # if we're on darwin, we might have darwin-rebuild or the distro id will be 'darwin'
        platform = FlakeOutputs.DARWIN
    else:
        # in all other cases of linux
        platform = FlakeOutputs.HOME_MANAGER
    return platform


def get_default_host():
    user_id = cmd.getout(["id", "-un"])
    user_name = os.getenv("USER") if user_id == "root" else user_id
    return f"{user_name}@{SYSTEM_ARCH}-{SYSTEM_OS}"


PLATFORM = get_flake_platform()
DEFAULT_HOST = get_default_host()


def change_workdir(func):
    @wraps(func)
    def wrapper(*args, **kw):
        old_workdir = os.getcwd()
        if "workdir" in kw:
            new_workdir = os.path.abspath(kw["workdir"])
        elif len(args) >= 2 and os.path.isdir(args[1]):
            new_workdir = os.path.abspath(args[1])
        elif DOTFILES:
            new_workdir = os.path.abspath(DOTFILES)
        is_change = new_workdir != old_workdir
        if is_change:
            os.chdir(new_workdir)
        result = func(*args, **kw)
        if is_change:
            os.chdir(old_workdir)
        return result

    return wrapper


@app.command(
    help="update all flake inputs or optionally specific flakes",
)
@change_workdir
def update(
    flake: List[str] = typer.Option(
        None,
        "--flake",
        "-f",
        metavar="[FLAKE]",
        help="specify an individual flake to be updated",
    ),
    not_flake: List[str] = typer.Option(
        None,
        "--no-flake",
        "-n",
        metavar="[FLAKE]",
        help="Don't update the following flake",
    ),
    stable: bool = typer.Option(
        False,
        "--stable",
        "-s",
        help="Update only flake-inputs that are currently stable on the system",
    ),
    commit: bool = typer.Option(False, help="commit the updated lockfile"),
    dry_run: bool = typer.Option(False, help="Test the result"),
):
    flags = ["--commit-lock-file"] if commit else []
    flakes = []
    all_flakes = get_flake_inputs_by_nix()
    stable_input = "darwin-stable" if ISMAC else "nixos-stable"
    ignore_inputs = ["nixos-stable"] if ISMAC else ["darwin-stable", "darwin"]
    msg = None
    if flake:
        for i in flake:
            if i in all_flakes:
                flakes.append(i)
            else:
                fmt.error(
                    f"The flake({i}) does not exist, please check all_flake or update it."
                )
                fmt.error(
                    f'Currently supported input-flakes are: {" ".join(all_flakes)}'
                )
                raise typer.Abort()
    elif not_flake:
        flakes = all_flakes
        for i in not_flake:
            if i in flakes:
                flakes.remove(i)
            else:
                fmt.warn(f"The flake({i}) does not exist, will ignore it.")
    else:
        msg = "updating all flake inputs"
        flakes = all_flakes
    for i in ignore_inputs:
        if i in flakes:
            flakes.remove(i)
    if stable:
        if stable_input not in flakes and stable_input in all_flakes:
            flakes.append(stable_input)
    elif stable_input in flakes:
        flakes.remove(stable_input)
    inputs = [f"--update-input {input}" for input in flakes]
    fmt.info(f"updating {','.join(flakes)}" if msg is None else msg)
    run_cmd(["nix", "flake", "lock"] + inputs + flags, dry_run=dry_run, shell=True)


# HACK: When macos is updated it automatically generates new /etc/shells,
# causing the nix-darwin build to fail
def shell_backup():
    etc_shell = "/etc/shells"
    if os.path.exists(etc_shell) and (not os.path.islink(etc_shell)):
        cmd.test(["sudo", "mv", "-vf", etc_shell, "/etc/shells.backup"])


def select(nixos: bool, darwin: bool, home: bool):
    if sum([nixos, darwin, home]) > 1:
        fmt.error(
            "Can't apply more than one of [--nixos, --darwin, --home]. aborting..."
        )
        raise typer.Abort()
    if nixos:
        return FlakeOutputs.NIXOS
    elif darwin:
        return FlakeOutputs.DARWIN
    elif home:
        return FlakeOutputs.HOME_MANAGER
    else:
        return PLATFORM


@app.command(
    help="Builds an initial Configuration", hidden=PLATFORM == FlakeOutputs.NIXOS
)
@change_workdir
def bootstrap(
    host: str = typer.Argument(
        DEFAULT_HOST, help="The hostname of the configuration to build"
    ),
    nixos: bool = False,
    darwin: bool = False,
    home: bool = False,
    remote: bool = typer.Option(
        default=False, help="Whether to fetch current changes from the remote"
    ),
    debug: bool = False,
    dry_run: bool = typer.Option(False, help="Test the result"),
    extra_args: List[str] = typer.Option(
        None, "--args", "-a", metavar="[AGES]", help="nix additional parameters"
    ),
):
    cfg = select(nixos=nixos, darwin=darwin, home=home)
    flags = [
        "-v",
        "--experimental-features",
        "nix-command flakes",
        "--extra-substituters",
        "https://shanyouli.cachix.org",
        "--impure",
    ]
    flags += extra_args if extra_args else []
    flags += ["--show-trace", "-L"] if debug else []
    bootstrap_flake = REMOTE_FLAKE if remote else get_flake(True)
    if host is None:
        fmt.error("Host unspecified")
        return
    if cfg is None:
        fmt.error("Missing configuration")
        raise typer.Abord()
    elif cfg == FlakeOutputs.NIXOS:
        fmt.error("Bootstrap does not apply to nixos system.")
        raise typer.Abort()
    elif cfg == FlakeOutputs.DARWIN:
        shell_backup()
        flake = f"{bootstrap_flake}#{cfg.value}.{host}.config.system.build.toplevel"
        nix = "nix" if cmd.exists("nix") else "/nix/var/nix/profiles/default/bin/nix"
        run_cmd([nix, "build", flake] + flags, dry_run)
        run_cmd(
            f"./result/sw/bin/darwin-rebuild switch --flake {bootstrap_flake}#{host}".split(),
            dry_run,
        )
    elif cfg == FlakeOutputs.HOME_MANAGER:
        try:
            from sd.api.macos import diskSetup

            diskSetup()
        except ModuleNotFoundError as e:
            fmt.error(e)
        flake = f"{bootstrap_flake}#{host}"
        cmd_list = (
            ["nix", "run"]
            + flags
            + [
                "github:nix-community/home-manager",
                "--no-write-lock-file",
                "--",
                "switch",
                "--flake",
                flake,
                "-b",
                "backup",
            ]
        )
        run_cmd(cmd_list, dry_run)
    else:
        fmt.error("Could not infer system type.")
        raise typer.Abord()


@app.command(help="builds the specified flake output")
def build(
    host: str = typer.Argument(DEFAULT_HOST, help="the hostname to build"),
    remote: bool = typer.Option(False, help="whether to fetch from the remote"),
    nixos: bool = False,
    darwin: bool = False,
    home: bool = False,
    debug: bool = True,
    dry_run: bool = typer.Option(False, help="Test the result"),
    extra_args: List[str] = typer.Option(
        None, "--args", "-a", metavar="[AGES]", help="nix additional parameters"
    ),
):
    cfg = select(nixos=nixos, darwin=darwin, home=home)
    if cfg is None:
        return
    elif cfg == FlakeOutputs.NIXOS:
        cmd_list = ["sudo", "nixos-rebuild", "build", "--flake"]
    elif cfg == FlakeOutputs.DARWIN:
        cmd_list = ["darwin-rebuild", "build", "--flake"]
    elif cfg == FlakeOutputs.HOME_MANAGER:
        cmd_list = ["home-manager", "built", "--flake"]
    else:
        fmt.error("could not infer system type.")
        raise typer.Abort()
    flake = f"{REMOTE_FLAKE if remote else get_flake()}#{host}"
    flags = ["--impure"]
    flags += ["--show-trace", "-L"] if debug else []
    flags += extra_args if extra_args else []
    cmd_list += cmd_list + [flake] + flags
    run_cmd(cmd_list, dry_run)


@app.command(help="builds and activates the specified flake output")
def switch(
    host: str = typer.Argument(DEFAULT_HOST, help="the hostname to build"),
    remote: bool = typer.Option(False, help="Whether to fetch from the remote"),
    nixos: bool = False,
    darwin: bool = False,
    home: bool = False,
    debug: bool = False,
    dry_run: bool = typer.Option(False, help="Test the result"),
    extra_args: List[str] = typer.Option(
        None, "--args", "-a", metavar="[AGES]", help="nix additional parameters"
    ),
):
    if not host:
        fmt.error("Error: host configuration not specified.")
        raise typer.Abort()

    cfg = select(nixos=nixos, darwin=darwin, home=home)
    if cfg is None:
        return
    elif cfg == FlakeOutputs.NIXOS:
        cmd_str = "sudo nixos-rebuild switch --flake"
    elif cfg == FlakeOutputs.DARWIN:
        shell_backup()
        cmd_str = "darwin-rebuild switch --flake"
    elif cfg == FlakeOutputs.HOME_MANAGER:
        cmd_str = "home-manager switch --flake"
    else:
        typer.secho("could not infer system type.", fg=Colors.ERROR.value)
        raise typer.Abort()
    flake = [f"{REMOTE_FLAKE}#{host}"] if remote else [f"{get_flake()}#{host}"]
    flags = ["--impure"]
    flags += ["--show-trace", "-L"] if debug else []
    flags += extra_args if extra_args else []
    cmd_list = cmd_str.split() + flake + flags
    run_cmd(cmd_list, dry_run)


@app.command(help="remove previously built configurations and symlinks from DOTFILES")
@change_workdir
def clean(
    filename: str = typer.Argument(
        "result", help="the filename to be cleaned, or '*' for all files"
    ),
    dry_run: bool = typer.Option(False, help="Test the result"),
):
    cmd_list = f"find . -type l -maxdepth 1 -name {filename} -exec rm {{}} +".split()
    run_cmd(cmd_list, dry_run)


@app.command(help="pull changes from remote repo")
@change_workdir
def pull(dry_run: bool = typer.Option(False, help="Test the result")):
    cmd_str = "git stash && git pull && git stash apply"
    run_cmd(cmd_str.split(), dry_run)


@app.command(help="cache the output environment of flake.nix")
@change_workdir
def cache(
    cache_name: str = "shanyouli",
    dry_run: bool = typer.Option(False, help="Test the result"),
):
    cmd_str = f"nix flake archive --json | jq -r '.path,(.inputs|to_entries[].value.path)' | cachix push {cache_name}"
    run_cmd(cmd_str.split(), shell=True)


@app.command(help="nix repl")
@change_workdir
def repl(
    pkgs: bool = typer.Option(False, help="import <nixpkgs>"),
    flake: bool = typer.Option(False, help="Automatically import build flake"),
    dry_run: bool = typer.Option(False, help="Test the result"),
):
    cmd_str = "nix repl --expr "
    exarg = "import <nixpkgs> {}" if pkgs else None
    if flake:
        flake_dir = os.getcwd()
        exarg = f"""
        let mysrc = builtins.getFlake "{flake_dir}";
            lib = mysrc.inputs.nixpkgs.lib.extend (self: super: {{
              my = import "{flake_dir}/lib" {{
                inherit (mysrc) inputs;
                lib = self;
              }};
            }});
            platform = mysrc.{PLATFORM.value}."{DEFAULT_HOST}";
            myPlatForm = {{
                inherit lib;
                inherit mysrc;
                inherit (platform) config options system _module;
                pkgs = { exarg if exarg else "platform.pkgs"};
            }};
        in myPlatForm
        """
    cmd_str += "'" + exarg + "'" if exarg else "builtins"
    if dry_run:
        fmt.info(f"> {cmd_str}")
    else:
        os.system(cmd_str)
