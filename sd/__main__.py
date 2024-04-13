#!/usr/bin/env python3
import json
import os
import re
import subprocess
from functools import wraps
from pathlib import Path
from typing import List

import typer

from sd.api import env, macbid, macos, nix
from sd.utils.enums import (
    ISLINUX,
    ISMAC,
    SYSTEM_ARCH,
    SYSTEM_OS,
    USERNAME,
    Colors,
    FlakeOutputs,
)

app = typer.Typer(add_completion=True)
app.add_typer(
    macbid.app,
    name="bid",
    help="Get macos App BundleID!",
    hidden=not ISMAC,
)
app.add_typer(
    env.app,
    name="env",
    help="save shell environment variable",
)  #  callback=env_app_callback

app.add_typer(
    macos.app,
    name="darwin",
    help="macos Commonly used shortcut commands",
    hidden=not ISMAC,
)

app.add_typer(nix.app, name="sys", help="System Configuration Management By Nix")


if __name__ == "__main__":
    app()
