#!/usr/bin/env python3

import typer

from sd.api import env, macbid, macos, nix
from sd.utils.enums import (
    ISMAC,
)

app = typer.Typer(add_completion=True)
app.add_typer(
    macbid.app,
    name='bid',
    help='Get macos App BundleID!',
    hidden=not ISMAC,
)
app.add_typer(
    env.app,
    name='env',
    help='save shell environment variable',
)  #  callback=env_app_callback

app.add_typer(
    macos.app,
    name='darwin',
    help='macos Commonly used shortcut commands',
    hidden=not ISMAC,
)

app.add_typer(nix.app, name='sys', help='System Configuration Management By Nix')


if __name__ == '__main__':
    app()
