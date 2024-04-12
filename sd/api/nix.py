import os
from functools import wraps
from subprocess import SubprocessError
from typing import List

import typer
from sd.api.macos import diskSetup
from sd.utils import cmd, fmt
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
        if dry_run:
            fmt.info(cmd.fmt([nix, "build", flake] + flags))
            fmt.info(
                f"./result/sw/bin/darwin-rebuild switch --flake {bootstrap_flake}#{host}"
            )
        else:
            cmd.run([nix, "build", flake] + flags)
            cmd.run(
                f"./result/sw/bin/darwin-rebuild switch --flake {bootstrap_flake}#{host}".split()
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
        if dry_run:
            fmt.info(cmd.fmt(cmd_list))
        else:
            cmd.run(cmd_list)
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
    if dry_run:
        fmt.info(cmd.fmt(cmd_list))
    else:
        cmd.run(cmd_list)


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
    if dry_run:
        fmt.info(cmd.fmt(cmd_list))
    else:
        cmd.run(cmd_list)


@app.command(help="remove previously built configurations and symlinks from DOTFILES")
@change_workdir
def clean(
    filename: str = typer.Argument(
        "result", help="the filename to be cleaned, or '*' for all files"
    ),
    dry_run: bool = typer.Option(False, help="Test the result"),
):
    cmd_list = f"find . -type l -maxdepth 1 -name {filename} -exec rm {{}} +".split()
    if dry_run:
        fmt.info(cmd.fmt(cmd_list))
    else:
        cmd.run(cmd_list)
