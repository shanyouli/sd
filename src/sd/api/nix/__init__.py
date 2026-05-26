import subprocess
from typing import Any, List, cast

import typer
import typer.completion
from typer._completion_shared import Shells

from sd.api.nix import nh as nh_backend
from sd.api.nix import nix as nix_backend
from sd.api.nix.common import (
    DEFAULT_HOST,
    DOTFILES,
    NIX_PROFILES,
    NIX_USER_PROFILES,
    PLATFORM,
    Gc,
    Generation,
    change_workdir,
    format_generation,
    get_current_generation,
    get_default_host,
    get_flake,
    get_flake_inputs_by_lock,
    get_flake_inputs_by_nix,
    get_flake_platform,
    get_generations,
    get_hm_profiles_root,
    get_re_compile,
    nix_diff,
    nix_install_profiles,
    nix_is_lix,
    nix_version_is_greater,
    nix_version_str,
    select,
    shell_backup,
)
from sd.utils import cmd, fmt
from sd.utils.enums import ISMAC, REMOTE_FLAKE, SYSTEM_ARCH, SYSTEM_OS, FlakeOutputs

__all__ = [
    "DEFAULT_HOST",
    "DOTFILES",
    "FlakeOutputs",
    "Gc",
    "Generation",
    "ISMAC",
    "NIX_PROFILES",
    "NIX_USER_PROFILES",
    "PLATFORM",
    "REMOTE_FLAKE",
    "SYSTEM_ARCH",
    "SYSTEM_OS",
    "app",
    "bootstrap",
    "build",
    "cache",
    "change_workdir",
    "clean",
    "diff",
    "format_generation",
    "gc",
    "get_current_generation",
    "get_default_host",
    "get_flake",
    "get_flake_inputs_by_lock",
    "get_flake_inputs_by_nix",
    "get_flake_platform",
    "get_generations",
    "get_hm_profiles_root",
    "get_re_compile",
    "init",
    "install",
    "nix_diff",
    "nix_install_profiles",
    "nix_is_lix",
    "nix_version_is_greater",
    "nix_version_str",
    "pull",
    "repl",
    "select",
    "shell_backup",
    "show",
    "switch",
    "update",
]

app = typer.Typer(
    add_completion=False, no_args_is_help=True
)  # add_completion 为 True 时表示使用默认补全
app_completion = typer.Typer(
    help="Generate and install completion scripts.", hidden=True
)
app.add_typer(app_completion, name="completion")


@app_completion.command(
    no_args_is_help=True,
    help="Show completion for the specified shell, to copy or customize it.",
)
def show(ctx: typer.Context, shell: Shells) -> None:
    typer.completion.show_callback(ctx, cast(Any, None), shell)


@app_completion.command(
    no_args_is_help=True, help="Install completion for the specified shell."
)
def install(ctx: typer.Context, shell: Shells) -> None:
    typer.completion.install_callback(ctx, cast(Any, None), shell)


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
    all_update: bool = typer.Option(False, "--all", "-a", help="Update all inputs."),
    commit: bool = typer.Option(False, help="commit the updated lockfile"),
    dry_run: bool = typer.Option(False, help="Test the result"),
):
    flags = ["--commit-lock-file"] if commit else []
    flakes = []
    # 使用 flake.lock 读取 inputs，避免 nix-repl 报错时拖慢 inputs 查询。
    if all_update:
        cmd.run(["nix", "flake", "update"] + flags, dry_run=dry_run, shell=True)
        return None
    all_flakes = get_flake_inputs_by_lock()
    ignore_inputs = ["nixos-stable", "darwin-stable", "darwin", "home-manager"]
    msg = None
    if flake:
        for i in flake:
            if i in all_flakes:
                flakes.append(i)
            elif i == "stable":
                flakes.append("home-manager")
                if ISMAC:
                    flakes.append("darwin-stable")
                    flakes.append("darwin")
                else:
                    flakes.append("nixos-stable")
            else:
                fmt.error(
                    f"The flake({i}) does not exist, please check all_flake or update it."
                )
                fmt.error(
                    f"Currently supported input-flakes are: {' '.join(all_flakes)}"
                )
                raise typer.Abort()
    all_flakes = (
        all_flakes if stable else [i for i in all_flakes if i not in ignore_inputs]
    )
    if not_flake:
        flakes = all_flakes
        for i in not_flake:
            if i in flakes:
                flakes.remove(i)
            else:
                fmt.warn(f"The flake({i}) does not exist, will ignore it.")
    else:
        msg = "updating all flake inputs"
        flakes = flakes if flakes else all_flakes
    fmt.info(f"updating {','.join(flakes)}" if msg is None else msg)
    is_greater_2_18 = nix_version_is_greater("2.18")
    if is_greater_2_18:
        cmd.run(
            ["nix", "flake", "update"] + flakes + flags, dry_run=dry_run, shell=True
        )
    else:
        inputs = [f"--update-input {input_name}" for input_name in flakes]
        cmd.run(["nix", "flake", "lock"] + inputs + flags, dry_run=dry_run, shell=True)


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
        '"nix-command flakes"',
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
        raise typer.Abort()
    if cfg == FlakeOutputs.NIXOS:
        fmt.error("Bootstrap does not apply to nixos system.")
        raise typer.Abort()
    if cfg == FlakeOutputs.DARWIN:
        shell_backup()
        flake = f"{bootstrap_flake}#{cfg.value}.{host}.config.system.build.toplevel"
        nix_default_bin = NIX_PROFILES.joinpath("default", "bin", "nix")
        if cmd.exists("nix"):
            nix_cmd = "nix"
        elif nix_default_bin.exists():
            nix_cmd = nix_default_bin.as_posix()
        else:
            fmt.error("Please install nix.")
            raise typer.Abort()
        cmd_result = cmd.run(
            [nix_cmd, "build", flake] + flags, dry_run=dry_run, shell=True
        )
        if cmd_result is None or cmd_result.returncode == 0:
            cmd.run(
                f"sudo ./result/sw/bin/darwin-rebuild switch --flake {bootstrap_flake}#{host}".split(),
                dry_run=dry_run,
            )
        else:
            raise subprocess.SubprocessError(cmd_result)
    elif cfg == FlakeOutputs.HOME_MANAGER:
        try:
            from sd.api.macos import diskSetup

            diskSetup()
        except ModuleNotFoundError as e:
            fmt.error(str(e))
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
        use_home = cfg == FlakeOutputs.HOME_MANAGER
        old_generation = get_current_generation(use_home)
        cmd.run(cmd_list, dry_run=dry_run)
        nix_diff(use_home=use_home, dry_run=dry_run, old_generation=old_generation)
    else:
        fmt.error("Could not infer system type.")
        raise typer.Abort()


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
    if nh_backend.has_nh():
        nh_backend.build_with_nh(cfg, host, remote, debug, dry_run, extra_args)
    else:
        nix_backend.build_with_nix(cfg, host, remote, debug, dry_run, extra_args)


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
    if nh_backend.has_nh():
        nh_backend.switch_with_nh(cfg, host, remote, debug, dry_run, extra_args)
    else:
        nix_backend.switch_with_nix(cfg, host, remote, debug, dry_run, extra_args)


@app.command(help="Showing different information for the two latest builds")
def diff(home: bool = False, dry_run: bool = False):
    nix_diff(use_home=home, dry_run=dry_run)


@app.command(help="remove previously built configurations and symlinks from DOTFILES")
@change_workdir
def clean(
    filename: str = typer.Argument(
        "result", help="the filename to be cleaned, or '*' for all files"
    ),
    dry_run: bool = typer.Option(False, help="Test the result"),
):
    cmd_list = f"find . -type l -maxdepth 1 -name {filename} -exec rm {{}} +".split()
    cmd.run(cmd_list, dry_run=dry_run)


@app.command(help="pull changes from remote repo")
@change_workdir
def pull(dry_run: bool = typer.Option(False, help="Test the result")):
    cmd_str = "git stash && git pull && git stash apply"
    cmd.run(cmd_str, shell=True, dry_run=dry_run)


@app.command(help="cache the output environment of flake.nix")
@change_workdir
def cache(
    cache_name: str = "shanyouli",
    dry_run: bool = typer.Option(False, help="Test the result"),
):
    cmd_str = f"nix flake archive --json | jq -r '.path,(.inputs|to_entries[].value.path)' | cachix push {cache_name}"
    cmd.run(cmd_str.split(), shell=True, dry_run=dry_run)


@app.command(help="nix repl")
def repl(
    pkgs: bool = typer.Option(False, help="import <nixpkgs>"),
    unstable: bool = typer.Option(False, help="import <nixpkgs-unstable>"),
    flake: bool = typer.Option(False, help="Automatically import build flake"),
    dry_run: bool = typer.Option(False, help="Test the result"),
):
    if flake and not pkgs and not unstable and nh_backend.has_nh():
        cfg = select(nixos=False, darwin=False, home=False)
        if cfg is not None:
            nh_backend.repl_with_nh(cfg, dry_run)
            return
    nix_backend.repl_with_nix(pkgs, unstable, flake, dry_run)


@app.command(
    help="run garbage collection on unused nix store paths",
    # no_args_is_help=True,
)
def gc(
    delete_older_than: str = typer.Option(
        None,
        "--delete-older-than",
        "-d",
        metavar="[AGE]",
        help="specify minimum age for deleting store paths",
    ),
    save: int = typer.Option(
        3, "--save", "-s", help="Save the last x number of builds"
    ),
    dry_run: bool = typer.Option(False, help="test the result of garbage collection"),
    # only: bool = typer.Option(False, help='Keep only one build'),
):
    if delete_older_than:
        base_cmd = f"nix-collect-garbage --delete-older-then {delete_older_than} {'--dry-run' if dry_run else ''}"
        cmd.run(["sudo"] + base_cmd.split(), dry_run=dry_run)
    else:
        nix_gc = Gc(dry_run=dry_run, save_num=save)
        nix_gc.gc_clear_list()
        nix_gc.run()


@app.command(help="Reinitialize darwin", hidden=PLATFORM != FlakeOutputs.DARWIN)
def init(
    host: str = typer.Argument(
        DEFAULT_HOST, help="the hostname of the configuration to build"
    ),
    dry_run: bool = typer.Option(False, help="Test the result of init"),
):
    if PLATFORM != FlakeOutputs.DARWIN:
        fmt.error("command is only supported on macos.")
        raise typer.Abort()
    nixgc = Gc(dry_run=dry_run, default="default")
    nixgc.clear_remove_default()
    nix_install_profiles(dry_run)
    nixgc.clear_remove_default(True)
    nixgc.run()
    bootstrap(host=host, darwin=True, remote=False, extra_args=None, dry_run=dry_run)


if __name__ == "__main__":
    typer.completion.completion_init()
    app()
