import typer
from sd.utils import cmd, fmt

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


if __name__ == "__main__":
    app()
