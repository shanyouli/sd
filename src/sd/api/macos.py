import typer
import plistlib
import tempfile
from pathlib import Path
from sd.utils import cmd, fmt, path, macutils

app = typer.Typer()


@app.command(help="Configure disk setup for nix-darwin")
def diskSetup():
    if not cmd.test("grep -q ^run\\b /etc/synthetic.conf".split()):
        APFS_UTIL = "/System/Library/Filesystems/apfs.fs/Contents/Resources/apfs.util"
        fmt.info("setting up /etc/synthetic.conf")
        cmd.run(
            "echo 'run\tprivate/var/run' | sudo tee -a /etc/synthetic.conf".split(),
            shell=True,
        )
        cmd.run([APFS_UTIL, "-B"])
        cmd.run([APFS_UTIL, "-t"])
    if not cmd.run(["test", "-L", "/run"]):
        fmt.info("linking /run directory")
        cmd.run("sudo ln -sfn private/var/run /run".split())
    fmt.success("disk setup complete")


@app.command(help="sync all.app to other file")
def syncapps(
    source: str = typer.Argument(None, help="source path"),
    target: str = typer.Argument(None, help="target path."),
):
    macutils.sync_trampolines(source, target)


@app.command(help="make alias, When target is None, it means get the original path.")
def alias(
    source: str = typer.Argument(None, help="source paths"),
    target: str = typer.Argument(None, help="alias target path."),
):
    source = path.abspath(source)
    if target is None:
        if (
            path.is_file(source)
            and cmd.run(
                f"file {source} | grep 'MacOS Alias file' >/dev/null"
            ).returncode
            == 0
        ):
            source_path = cmd.getout(f"""osascript <<EOF
tell application "Finder"
    set theItem to (POSIX file "{source}") as alias
    if the kind of theItem is "alias" then
        get the POSIX path of ((original item of theItem) as text)
    end if
end tell
EOF
            """)
            fmt.info(f"The alias for file {source} is {source_path}")
            return source_path
        else:
            fmt.error(f"{source} Not an alias file")
            return source
    target = path.abspath(target)

    if not path.is_exist(source):
        fmt.error(f"Please Confirm the existence of path {source}.")
        raise typer.Abort()

    if path.is_exist(target):
        fmt.error(
            f"{target} is exist, Overwriting operations are not allowed, resulting in the loss of important files."
        )
        raise typer.Abort()
    target_parent = path.get_parent(target).as_posix()
    path.mkdir(target_parent)
    fmt.info(f"make alias from {source} to {target}")
    if cmd.exists("mkalias"):
        cmd.run(["mkalias", source, target])
    else:
        cmd.run(f"""osascript <<EOF
tell application "Finder"
    set originalPath to POSIX file "{source}"
    set aliasPath to POSIX file "{target_parent}"
    make alias file to originalPath at aliasPath
    set name of result to "{Path(target).name}"
end tell
EOF
        """)


@app.command(help="Docker restart")
def refresh(
    rd: bool = typer.Option(
        False, help="Redirect the bundle id to specify the version"
    ),
):
    cmd.run(
        [
            "defaults",
            "write",
            "com.apple.dock",
            "ResetLaunchPad",
            "-bool",
            "true",
            "&&",
            "killall",
            "Dock",
        ],
        shell=True,
    )
    if rd:
        cmd.run(
            [
                "/System/Library/Frameworks/CoreServices.framework/Versions/A/Frameworks/LaunchServices.framework/Versions/A/Support/lsregister",
                "-kill",
                "-r",
                "-domain local",
                "-domain",
                "system",
                "-domain",
                "user",
            ],
            shell=True,
        )


@app.command(help="toggle to set proxy for org.nixos.nix-daemon.plist")
def proxy(url: str = typer.Option("", help="proxy url")):
    """
    @see https://github.com/ryan4yin/nix-darwin-kickstarter/blob/main/rich-demo/scripts/darwin_set_proxy.py
    """
    NIX_DAEMON_PLIST = Path("/Library/LaunchDaemons/org.nixos.nix-daemon.plist")
    if not NIX_DAEMON_PLIST.exists():
        fmt.error("Please install the nix service first.")
        raise typer.Abort()
    if url != "" and "://" not in url:
        fmt.error(
            "The url format is not legal, please use the correct format, eg: http://xx.xx.xx:port"
        )
        raise typer.Abort()
    pl = plistlib.loads(NIX_DAEMON_PLIST.read_bytes())
    pl_environment_variables = pl.get("EnvironmentVariables")
    if pl_environment_variables:
        if url == "":
            if pl_environment_variables.get("http_proxy"):
                pl_environment_variables.pop("http_proxy")
                pl_environment_variables.pop("https_proxy")
            else:
                pl_environment_variables["http_proxy"] = "http://127.0.0.1:10801"
                pl_environment_variables["https_proxy"] = "http://127.0.0.1:10801"
        else:
            pl_environment_variables["http_proxy"] = url
            pl_environment_variables["https_proxy"] = url
            pl["EnvironmentVariables"] = pl_environment_variables
    else:
        pl["EnvironmentVariables"] = dict()
        pl["EnvironmentVariables"]["http_proxy"] = (
            url if url else "http://127.0.0.1:10801"
        )
        pl["EnvironmentVariables"]["https_proxy"] = (
            url if url else "http://127.0.0.1:10801"
        )
    with tempfile.NamedTemporaryFile(delete=False) as fb:
        fb.write(plistlib.dumps(pl))
        cmd.run(["sudo", "mv", "-f", fb.name, NIX_DAEMON_PLIST._str], show=True)
        cmd.run(["sudo", "chmod", "444", NIX_DAEMON_PLIST._str], show=True)
        cmd.run(["sudo", "chown", "-R", "root", NIX_DAEMON_PLIST._str], show=True)
        cmd.run(["sudo", "launchctl", "unload", "-w", NIX_DAEMON_PLIST._str], show=True)
        cmd.run(["sudo", "launchctl", "load", "-w", NIX_DAEMON_PLIST._str], show=True)


if __name__ == "__main__":
    app()
