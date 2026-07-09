import os

import typer

from sd.api.nix.common import (
    flake_skip_worktree_guard,
    get_current_generation,
    get_flake,
    nix_diff,
    shell_backup,
)
from sd.utils import cmd, fmt
from sd.utils.enums import FlakeOutputs


def build_with_nix(
    cfg: FlakeOutputs,
    host: str,
    debug: bool,
    dry_run: bool,
    extra_args: list[str] | None,
):
    flake_root = get_flake()
    with flake_skip_worktree_guard(flake_root, debug=debug):
        if cfg == FlakeOutputs.NIXOS:
            cmd_list = ["sudo", "nixos-rebuild", "build", "--flake"]
        elif cfg == FlakeOutputs.DARWIN:
            cmd_list = ["sudo", "darwin-rebuild", "build", "--flake"]
        elif cfg == FlakeOutputs.HOME_MANAGER:
            cmd_list = ["home-manager", "build", "--flake"]
        else:
            fmt.error("could not infer system type.")
            raise typer.Abort()
        flake = f"{flake_root}#{host}"
        flags = ["--impure"]
        flags += ["--show-trace", "-L"] if debug else []
        flags += extra_args if extra_args else []
        cmd_list += [flake] + flags
        use_home = cfg == FlakeOutputs.HOME_MANAGER
        old_generation = get_current_generation(use_home)
        result_out = cmd.run(cmd_list, dry_run=dry_run)
        if dry_run or (result_out and result_out.returncode == 0):
            nix_diff(use_home=use_home, dry_run=dry_run, old_generation=old_generation)


def switch_with_nix(
    cfg: FlakeOutputs,
    host: str,
    debug: bool,
    dry_run: bool,
    extra_args: list[str] | None,
):
    flake_root = get_flake()
    with flake_skip_worktree_guard(flake_root, debug=debug):
        if cfg == FlakeOutputs.NIXOS:
            cmd_str = "sudo nixos-rebuild switch --flake"
        elif cfg == FlakeOutputs.DARWIN:
            shell_backup()
            cmd_str = "sudo darwin-rebuild switch --flake"
        elif cfg == FlakeOutputs.HOME_MANAGER:
            cmd_str = "home-manager switch --flake"
        else:
            fmt.error("could not infer system type.")
            raise typer.Abort()
        flake = [f"{flake_root}#{host}"]
        flags = ["--impure"]
        flags += ["--show-trace", "-L"] if debug else []
        flags += extra_args if extra_args else []
        cmd_list = cmd_str.split() + flake + flags
        use_home = cfg == FlakeOutputs.HOME_MANAGER
        old_generation = get_current_generation(use_home)
        hm_generation = get_current_generation(True)
        result_out = cmd.run(cmd_list, dry_run=dry_run)
        if dry_run or (result_out and result_out.returncode == 0):
            nix_diff(use_home=use_home, dry_run=dry_run, old_generation=old_generation)
            if old_generation != hm_generation:
                nix_diff(
                    use_home=(not use_home),
                    dry_run=dry_run,
                    old_generation=hm_generation,
                )


def repl_with_nix(
    pkgs: bool,
    unstable: bool,
    flake: bool,
    dry_run: bool,
):
    flake_root = get_flake() if flake else None
    workdir = flake_root if flake_root else os.getcwd()
    with flake_skip_worktree_guard(workdir, debug=False):
        cmd_str = "nix repl --expr "
        if pkgs:
            exarg = "import <nixpkgs> {}"
        elif unstable:
            exarg = "import <nixpkgs-unstable> {}"
        else:
            exarg = None
        if flake:
            cmd_str = f"nix --extra-experimental-features repl-flake repl {flake_root}"
        else:
            cmd_str += "'" + exarg + "'" if exarg else "builtins"
        if dry_run:
            fmt.info(f"> {cmd_str}")
        else:
            os.system(cmd_str)
