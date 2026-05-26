import typer

from sd.api.nix.common import get_current_generation, get_flake, nix_diff, shell_backup
from sd.utils import cmd, fmt
from sd.utils.enums import REMOTE_FLAKE, FlakeOutputs

NH_NAMESPACE_BY_OUTPUT = {
    FlakeOutputs.NIXOS: "os",
    FlakeOutputs.DARWIN: "darwin",
    FlakeOutputs.HOME_MANAGER: "home",
}


def has_nh() -> bool:
    return cmd.exists("nh")


def get_nh_namespace(cfg: FlakeOutputs) -> str:
    namespace = NH_NAMESPACE_BY_OUTPUT.get(cfg)
    if namespace is None:
        fmt.error("could not infer nh namespace.")
        raise typer.Abort()
    return namespace


def _flake_ref(remote: bool) -> str:
    return REMOTE_FLAKE if remote else get_flake()


def _config_flag(cfg: FlakeOutputs) -> str:
    return "--configuration" if cfg == FlakeOutputs.HOME_MANAGER else "--hostname"


def _nh_build_flags(debug: bool, dry_run: bool) -> list[str]:
    flags = ["--impure", "--diff", "never"]
    if dry_run:
        flags.append("--dry")
    if debug:
        flags += ["--show-trace", "-L"]
    return flags


def _nh_repl_flags() -> list[str]:
    return []


def _append_extra_args(cmd_list: list[str], extra_args: list[str] | None) -> list[str]:
    if extra_args:
        return cmd_list + ["--"] + extra_args
    return cmd_list


def build_with_nh(
    cfg: FlakeOutputs,
    host: str,
    remote: bool,
    debug: bool,
    dry_run: bool,
    extra_args: list[str] | None,
):
    namespace = get_nh_namespace(cfg)
    cmd_list = (
        ["nh", namespace, "build"]
        + _nh_build_flags(debug=debug, dry_run=dry_run)
        + [_config_flag(cfg), host, _flake_ref(remote)]
    )
    cmd_list = _append_extra_args(cmd_list, extra_args)
    use_home = cfg == FlakeOutputs.HOME_MANAGER
    old_generation = get_current_generation(use_home)
    result_out = cmd.run(cmd_list, dry_run=dry_run)
    if dry_run or (result_out and result_out.returncode == 0):
        nix_diff(use_home=use_home, dry_run=dry_run, old_generation=old_generation)


def switch_with_nh(
    cfg: FlakeOutputs,
    host: str,
    remote: bool,
    debug: bool,
    dry_run: bool,
    extra_args: list[str] | None,
):
    namespace = get_nh_namespace(cfg)
    if cfg == FlakeOutputs.DARWIN:
        shell_backup()
    cmd_list = (
        ["nh", namespace, "switch"]
        + _nh_build_flags(debug=debug, dry_run=dry_run)
        + [_config_flag(cfg), host, _flake_ref(remote)]
    )
    cmd_list = _append_extra_args(cmd_list, extra_args)
    use_home = cfg == FlakeOutputs.HOME_MANAGER
    old_generation = get_current_generation(use_home)
    hm_generation = get_current_generation(True)
    result_out = cmd.run(cmd_list, dry_run=dry_run)
    if dry_run or (result_out and result_out.returncode == 0):
        nix_diff(use_home=use_home, dry_run=dry_run, old_generation=old_generation)
        if old_generation != hm_generation:
            nix_diff(
                use_home=(not use_home), dry_run=dry_run, old_generation=hm_generation
            )


def repl_with_nh(cfg: FlakeOutputs, dry_run: bool):
    namespace = get_nh_namespace(cfg)
    cmd_list = ["nh", namespace, "repl"] + _nh_repl_flags() + [get_flake()]
    cmd.run(cmd_list, dry_run=dry_run)
