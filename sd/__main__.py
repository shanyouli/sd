#!/usr/bin/env python3

import typer

from sd.api import env, launchctl, macbid, macos, nix
from sd.utils import cmd
from sd.utils.enums import ISMAC

SYSAPP = None
if (
    cmd.exists('nixos-rebuild')
    or cmd.exists('darwin-rebuild')
    or cmd.exists('home-manager')
):
    app = nix.app
    SYSAPP = 'nix'

else:
    app = typer.Typer(no_args_is_help=True)
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
    no_args_is_help=True,
)
if SYSAPP != 'nix':
    app.add_typer(
        nix.app,
        name='nix',
        help='System Configuration Management By Nix',
        hidden=cmd.exists('nix'),
        no_args_is_help=True,
    )
if cmd.exists('launchctl'):
    app.add_typer(
        launchctl.app,
        name='sc',
        help='macos launchctl services manager',
        no_args_is_help=True,
    )
    app.add_typer(
        launchctl.app,
        name='service',
        help='macos launchctl services manager',
        no_args_is_help=True,
    )

if __name__ == '__main__':
    app()
