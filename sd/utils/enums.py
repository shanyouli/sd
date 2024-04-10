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


UNAME = platform.uname()
user_id = run(["id", "-un"], capture_output=True).stdout.decode().strip()

SYSTEM_OS = UNAME.system.lower()
SYSTEM_ARCH = "aarch64" if UNAME.machine == "arm64" else UNAME.machine
USERNAME = os.getenv("USER") if user_id == "root" else user_id

ISMAC = SYSTEM_OS == "darwin"
ISLINUX = SYSTEM_OS == "linux"
