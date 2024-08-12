#!/usr/bin/env python3

import typer
import sys

from sd.api import env, launchctl, macbid, macos, nix
from sd.utils import cmd
from sd.utils.enums import ISMAC

SYSAPP = None
if (
    cmd.exists("nixos-rebuild")
    or cmd.exists("darwin-rebuild")
    or cmd.exists("home-manager")
):
    app = nix.app
    SYSAPP = "nix"

else:
    import typer.completion
    from typer._completion_shared import Shells

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
        typer.completion.show_callback(ctx, None, shell)

    @app_completion.command(
        no_args_is_help=True, help="Install completion for the specified shell."
    )
    def install(ctx: typer.Context, shell: Shells) -> None:
        typer.completion.install_callback(ctx, None, shell)


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
    no_args_is_help=True,
)
if SYSAPP != "nix":
    app.add_typer(
        nix.app,
        name="nix",
        help="System Configuration Management By Nix",
        hidden=cmd.exists("nix"),
        no_args_is_help=True,
    )
if cmd.exists("launchctl"):
    app.add_typer(
        launchctl.app,
        name="sc",
        help="macos launchctl services manager",
        no_args_is_help=True,
    )
    app.add_typer(
        launchctl.app,
        name="service",
        help="macos launchctl services manager",
        no_args_is_help=True,
    )


def main():
    typer.completion.completion_init()
    sys.exit(app())


if __name__ == "__main__":
    main()
