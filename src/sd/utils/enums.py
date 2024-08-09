import os
import platform
from enum import Enum
from subprocess import run

from typer import colors


class Colors(Enum):
    SUCCESS = colors.GREEN
    INFO = colors.BLUE
    ERROR = colors.RED
    WARN = colors.YELLOW


class FlakeOutputs(Enum):
    NIXOS = "nixosConfigurations"
    DARWIN = "darwinConfigurations"
    HOME_MANAGER = "homeConfigurations"


class Dotfiles:
    @property
    def value(self):
        env_dotfiles = os.getenv("DOTFILES") or ""
        for i in [
            env_dotfiles,
            "/etc/dotfiles",
            "/etc/nixos",
            os.path.expanduser("~/.config/dotfiles"),
            os.path.expanduser("~/.dotfiles"),
            os.path.expanduser("~/.nixpkgs"),
        ]:
            if (
                os.path.isdir(i)
                and os.path.exists(os.path.join(i, "flake.nix"))
                and os.path.exists(os.path.join(i, ".git"))
            ):
                return os.path.realpath(i)


UNAME = platform.uname()
user_id = run(["id", "-un"], capture_output=True).stdout.decode().strip()

SYSTEM_OS = UNAME.system.lower()
SYSTEM_ARCH = "aarch64" if UNAME.machine == "arm64" else UNAME.machine
USERNAME = os.getenv("USER") if user_id == "root" else user_id

ISMAC = SYSTEM_OS == "darwin"
ISLINUX = SYSTEM_OS == "linux"

REMOTE_FLAKE = "github:shanyouli/dotfiles"
