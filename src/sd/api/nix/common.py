import getpass
import json
import os
import re
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from functools import wraps
from pathlib import Path
from subprocess import SubprocessError
from typing import List, cast

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
NIX_PROFILES = (
    Path(os.environ.get("NIX_STATE_HOME", "/nix/var/nix"))
    .expanduser()
    .joinpath("profiles")
)
NIX_USER_PROFILES = (
    Path(os.environ.get("XDG_STATE_HOME", "~/.local/state"))
    .expanduser()
    .joinpath("nix", "profiles")
)


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


def get_flake_inputs_by_lock(flake_path: Path | None | str = None) -> list[str]:
    flake_path = os.getcwd() if flake_path is None else flake_path
    flake_lock = os.path.join(os.path.realpath(flake_path), "flake.lock")
    data_json = path.json_read(flake_lock)
    if isinstance(data_json, dict):
        nodes = data_json.get("nodes")
        if isinstance(nodes, dict):
            nodes_dict = cast(dict[str, object], nodes)
            root = nodes_dict.get("root")
            if isinstance(root, dict):
                root_dict = cast(dict[str, object], root)
                inputs = root_dict.get("inputs")
                if isinstance(inputs, dict):
                    return [str(key) for key in inputs]
    fmt.error(f"Failed to read data from {flake_lock} file")
    raise typer.Abort()


def get_flake_inputs_by_nix(flake_path: Path | None | str = None):
    flake_path = os.getcwd() if flake_path is None else flake_path
    if path.is_file(os.path.join(os.path.realpath(flake_path), "flake.lock")):
        flake_json_text = cmd.getout(
            f"""nix eval --raw --impure --expr 'builtins.toJSON (builtins.getFlake "{flake_path}").inputs'"""
        )
        flake_json_list = []
        is_json_start = False
        for i in flake_json_text.splitlines():
            if is_json_start:
                flake_json_list.append(i)
            if "{" in i:
                is_json_start = True
                flake_json_list.append(i)
        return [i for i in json.loads("\n".join(flake_json_list))]

    fmt.error(f"The {flake_path} directory is not a nix-flake project")
    raise typer.Abort()


def get_flake_platform():
    if cmd.exists("nixos-rebuild"):
        platform = FlakeOutputs.NIXOS
    elif cmd.exists("darwin-rebuild") or ISMAC:
        platform = FlakeOutputs.DARWIN
    else:
        platform = FlakeOutputs.HOME_MANAGER
    return platform


def get_default_host():
    user_id = cmd.getout(["id", "-un"])
    user_name = os.getenv("USER") if user_id == "root" else user_id
    return f"{user_name}@{SYSTEM_ARCH}-{SYSTEM_OS}"


PLATFORM = get_flake_platform()
DEFAULT_HOST = get_default_host()


def _resolve_workdir(args: tuple[object, ...], kw: dict[str, object]) -> str:
    old_workdir = os.getcwd()
    if "workdir" in kw:
        workdir = kw["workdir"]
        if isinstance(workdir, (str, os.PathLike)):
            return os.path.abspath(workdir)
    elif len(args) >= 2 and os.path.isdir(args[1]):
        return os.path.abspath(args[1])
    elif DOTFILES:
        return os.path.abspath(DOTFILES)
    return old_workdir


def _get_skip_worktree_files(workdir: str) -> list[str]:
    try:
        output = cmd.getout(
            [
                "git",
                "-C",
                workdir,
                "ls-files",
                "-t",
                "--full-name",
                "--",
                "flake.nix",
                "flake.lock",
            ],
            shell=False,
            show=False,
        )
    except SubprocessError:
        return []

    skip_files: list[str] = []
    for line in output.splitlines():
        if not line:
            continue
        status, _, relpath = line.partition(" ")
        if status == "S" and relpath:
            skip_files.append(os.path.join(workdir, relpath))
    return skip_files


@contextmanager
def flake_skip_worktree_guard(workdir: str):
    workdir = os.path.abspath(workdir)
    restored_files: list[str] = []

    try:
        for filepath in _get_skip_worktree_files(workdir):
            cmd.run(
                ["git", "-C", workdir, "update-index", "--no-skip-worktree", filepath]
            )
            restored_files.append(filepath)

        yield
    finally:
        for filepath in restored_files:
            cmd.run(["git", "-C", workdir, "update-index", "--skip-worktree", filepath])


def change_workdir(func):
    @wraps(func)
    def wrapper(*args, **kw):
        old_workdir = os.getcwd()
        new_workdir = _resolve_workdir(args, kw)
        is_change = new_workdir != old_workdir
        try:
            if is_change:
                os.chdir(new_workdir)
            with flake_skip_worktree_guard(new_workdir):
                return func(*args, **kw)
        finally:
            if is_change:
                os.chdir(old_workdir)

    return wrapper


@dataclass
class Generation:
    version: int
    path: Path
    created_at: datetime


def get_hm_profiles_root() -> Path:
    # A copy of home-manager's profile root detection logic.
    global_nix_profiles_dir = NIX_PROFILES.joinpath(getpass.getuser())
    user_nix_profiles_dir = NIX_USER_PROFILES

    return (
        user_nix_profiles_dir
        if user_nix_profiles_dir.exists()
        else global_nix_profiles_dir
    )


def get_re_compile(use_home: bool):
    return re.compile(
        r"home-manager-(?P<number>\d+)-link"
        if use_home
        else r"system-(?P<number>\d+)-link"
    )


def get_generations(use_home: bool) -> List[Generation]:
    profile_regex = get_re_compile(use_home)
    profile_path = get_hm_profiles_root() if use_home else NIX_PROFILES
    generation_list = []
    for entry in profile_path.iterdir():
        result = profile_regex.search(str(entry))
        if result:
            version_number = int(result.groupdict()["number"])
            real_path = entry.resolve()
            created_at = datetime.fromtimestamp(os.path.getctime(real_path))

            generation = Generation(
                version=version_number, path=real_path, created_at=created_at
            )

            generation_list.append(generation)
    generation_list = sorted(generation_list, key=lambda g: g.version, reverse=True)

    return generation_list


def get_current_generation(use_home: bool) -> Generation | None:
    if use_home:
        profile_path = get_hm_profiles_root()
        base_name = "home-manager"
    else:
        profile_path = NIX_PROFILES
        base_name = "system"
    profile_regex = get_re_compile(use_home)
    if not profile_path.joinpath(base_name).exists():
        return None
    current_dir = str(profile_path.joinpath(base_name).readlink())
    if current_dir:
        result = profile_regex.search(current_dir)
        if result:
            version_number = int(result.groupdict()["number"])
            real_path = profile_path.joinpath(current_dir)
            created_at = datetime.fromtimestamp(os.path.getctime(real_path))
            return Generation(
                version=version_number, path=real_path, created_at=created_at
            )
    return None


def format_generation(generation: Generation) -> str:
    date_format = "%Y-%m-%d %H:%M"
    return (
        f"create time: {generation.created_at.strftime(date_format)}, "
        f"version: {generation.version}"
    )


def nix_diff(use_home: bool, dry_run: bool, old_generation: Generation | None = None):
    use_dix = 0
    if cmd.exists("dix"):
        use_dix = 1
    elif cmd.exists("nvd"):
        use_dix = 2
    else:
        return
    if old_generation:
        generation_first = old_generation
        generation_second = get_current_generation(use_home)
        if generation_second is None:
            return
    else:
        generations = get_generations(use_home)
        if generations is None or len(generations) < 2:
            fmt.info("No previous data available")
            return
        generation_first = generations[1]
        generation_second = generations[0]
    fmt.info(
        f"Previous build creation information {format_generation(generation_first)}"
    )
    fmt.info(f"Current build information {format_generation(generation_second)}")
    if use_dix == 1:
        cmd.run(
            ["dix", str(generation_first.path), str(generation_second.path)],
            dry_run=dry_run,
        )
    else:
        cmd.run(
            ["nvd", "diff", str(generation_first.path), str(generation_second.path)],
            dry_run=dry_run,
        )


class Gc:
    def __init__(
        self,
        dry_run: bool = True,
        re_pattern: str = r"(.*)-(\d+)-link$",
        save_num: int = 1,
        default: str = "default",
    ):
        self.dry_run = dry_run
        self.re_pattern = re.compile(re_pattern)
        self.save_num = save_num
        self.clear_list = []
        self.profiles = [
            i
            for i in [
                NIX_PROFILES,
                NIX_USER_PROFILES,
            ]
            if i.is_dir()
        ]
        self.gc_autos = [
            i
            for i in [
                Path(os.environ.get("NIX_STATE_HOME", "/nix/var/nix"))
                .expanduser()
                .joinpath("gcroots", "auto")
            ]
            if i.is_dir()
        ]
        self.default = default

    def remove_from_link_list(self):
        if self.clear_list:
            if self.dry_run:
                cdir = os.getcwd()
                fmt.info(f"The following files will be deleted{cdir} ..")
                for i in self.clear_list:
                    fmt.info(f"delete: {os.path.join(cdir, i)}")
            else:
                for i in self.clear_list:
                    path.remove_file_or_link(i)
        else:
            fmt.info("Not File will be deleted...")

    @change_workdir
    def gc_auto(self, profile: Path):
        store = {}
        self.clear_list = []
        for i in os.listdir():
            if path.is_link(i):
                target_path = path.readlink(i)
                if not path.is_exist(target_path):
                    self.clear_list.append(i)
                    continue
            f_prefix_num = self.re_pattern.match(target_path.name)
            if not f_prefix_num:
                store[target_path] = [(i, 1)]
                continue
            f_prefix = f_prefix_num.group(1)
            num = int(f_prefix_num.group(2))
            if f_prefix not in store:
                store[f_prefix] = [(i, num)]
            else:
                store[f_prefix].append((i, num))
        for i in store:
            store[i] = sorted(store[i], key=lambda k: k[-1], reverse=True)
            for cpath in store[i][self.save_num :]:
                self.clear_list.append(cpath[0])
        self.remove_from_link_list()

    @change_workdir
    def gc_profile(self, profile: Path):
        store = {}
        self.clear_list = []
        for i in os.listdir():
            if path.is_link(i):
                if not path.is_exist(path.readlink(i)):
                    self.clear_list.append(i)
                    continue
            f_prefix_num = self.re_pattern.match(i)
            if not f_prefix_num:
                continue
            f_prefix = f_prefix_num.group(1)
            num = int(f_prefix_num.group(2))
            if f_prefix not in store:
                store[f_prefix] = [(i, num)]
            else:
                store[f_prefix].append((i, num))
        for i in store.values():
            i = sorted(i, key=lambda k: k[-1], reverse=True)
            for cpath in i[self.save_num :]:
                self.clear_list.append(cpath[0])
        self.remove_from_link_list()

    def gc_clear_list(self):
        for i in self.gc_autos:
            self.gc_auto(i)
        for i in self.profiles:
            self.gc_profile(i)

    def clear_remove_default(self, reverse: bool = False):
        for i in self.gc_autos:
            for k in os.listdir(i):
                kpath = os.path.join(i, k)
                if not path.is_link(kpath):
                    continue
                is_p = path.readlink(kpath).name.startswith(self.default)
                is_p = (not is_p) if reverse else is_p
                if is_p:
                    if self.dry_run:
                        fmt.warn(f"Delete {kpath}")
                    else:
                        path.remove_file_or_link(kpath)
        for i in self.profiles:
            for k in os.listdir(i):
                kpath = os.path.join(i, k)
                is_p = os.path.basename(kpath).startswith(self.default)
                is_p = (not is_p) if reverse else is_p
                if is_p:
                    if self.dry_run:
                        fmt.warn(f"Delete {kpath}")
                    else:
                        path.remove_file_or_link(kpath)

    def run(self):
        cmd.run(["sudo", "nix", "store", "gc", "-v"], dry_run=self.dry_run)


def nix_version_str() -> str:
    """获取当前 nix version"""
    return cmd.getout(["nix", "--version"]).splitlines()[0].split()[-1]


def nix_is_lix() -> bool:
    return cmd.getout(["nix", "--version"]).splitlines()[0].find("Lix") != -1


def nix_version_is_greater(v: str) -> bool:
    current_version = [int(i) for i in nix_version_str().split(".")]
    ver = [int(i) for i in v.split(".")]
    v_len = len(ver)
    c_len = len(current_version)
    len_v = c_len if c_len <= v_len else v_len
    r = False
    for i in range(len_v):
        if current_version[i] is not None and ver[i] < current_version[i]:
            r = True
    else:
        if len_v != v_len:
            r = True
    return r


def nix_install_profiles(dry_run: bool = True):
    nix_profile = NIX_PROFILES.joinpath("default")
    nix_profile_str = nix_profile.as_posix()
    nix_version_line = cmd.getout(["nix", "--version"]).splitlines()[0]
    lix_latest_tag = cmd.get_latest_tag_by_git(
        "https://git.lix.systems/lix-project/lix"
    )
    extra_lix_args = [
        "--extra-substituters",
        "https://cache.lix.systems",
        "--extra-trusted-public-keys",
        "cache.lix.systems:aBnZUw8zA7H35Cz2RyKFVs3H4PlGTLawyY5KRbvJR8o=",
    ]
    base_run_cmd: list[str] = [
        "nix",
        "run",
        "--experimental-features",
        '"nix-command flakes"',
    ] + extra_lix_args
    base_cmd: list[str] = [
        "sudo",
        "nix",
        "upgrade-nix",
        "--profile",
        nix_profile_str,
        "--keep-outputs",
        "--keep-derivations",
        "--experimental-features",
        '"nix-command flakes"',
    ]
    if os.path.exists(os.path.join(nix_profile, "bin", "nix")):
        if nix_version_line.find("Lix") != -1:
            nix_versions = nix_version_line.split()[-1]
            if lix_latest_tag is not None and nix_versions != lix_latest_tag:
                cmd.run(
                    ["sudo", "-H", "--preserve-env=SSH+AUTH_SOCK"]
                    + base_run_cmd
                    + [
                        f"'git+https://git.lix.systems/lix-project/lix?ref=refs/tags/{lix_latest_tag}'",
                        "--",
                        "upgrade-nix",
                        "--porfile",
                        nix_profile_str,
                    ]
                    + extra_lix_args,
                    dry_run=dry_run,
                    shell=True,
                )
            else:
                cmd.run(base_cmd + extra_lix_args, dry_run=dry_run, shell=True)
        elif lix_latest_tag is not None:
            _path = f"{nix_profile.joinpath('bin').as_posix()}:$PATH"
            cmd.run(
                [
                    ("PATH='%s'" % _path),
                    "sudo",
                    "-H",
                    "--preserve-env=SSH+AUTH_SOCK",
                    "--preserve-env=PATH",
                ]
                + base_run_cmd
                + extra_lix_args,
                dry_run=dry_run,
                shell=True,
            )
        else:
            cmd.run(base_cmd, dry_run=dry_run, shell=True)
    else:
        cmd.run(
            [
                "sudo",
                "-H",
                "--preserve-env=SSH_AUTH_SOCK",
                "nix",
                "profile",
                "install",
                "--profile",
                nix_profile_str,
                (
                    f"git+https://git.lix.systems/lix-project/lix?ref=refs/tags/{lix_latest_tag}"
                    if lix_latest_tag
                    else "git+https://git.lix.systems/lix-project/lix"
                ),
                "--priority",
                "3",
            ]
            + extra_lix_args,
            dry_run=dry_run,
            shell=True,
        )


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
    if darwin:
        return FlakeOutputs.DARWIN
    if home:
        return FlakeOutputs.HOME_MANAGER
    return PLATFORM
