import plistlib
from pathlib import Path
from tempfile import mkdtemp

from sd.utils import cmd, fmt, path


def init_app(target_path: Path, appname: str = None, force: bool = False):
    target_app = (
        target_path if target_path.suffix == ".app" else target_path.joinpath(appname)
    )
    fmt.info(force)
    if target_app.exists():
        if force:
            fmt.warn("Target app already exists and will be deleted")
            cmd.getout(f"rm -rf '{target_app.absolute().as_posix()}'")
        else:
            fmt.error(f"Target file {target_app.as_posix()} already exists")
            return False
    target_app.mkdir(mode=0o755, parents=True)
    target_app.joinpath("Contents").mkdir(mode=0o755)
    for i in ["MacOS", "Resources"]:
        target_app.joinpath("Contents", i).mkdir(mode=0o755)
    return target_app


def create_main_by_shell(app_path: Path, target_app: Path):
    target_script = target_app.joinpath("Contents", "MacOS", "main")
    app_path_str = app_path.as_posix()
    with open(target_script, mode="w") as f:
        f.write(f"""#!/usr/bin/env bash
if [ $# -gt 0 ]; then
    open "{app_path_str}" --args "$@"
else
    open "{app_path_str}"
fi
        """)
    target_script.chmod(0o755)


def copy_Info(app: Path, target_app: Path):
    pl = plistlib.loads(app.joinpath("Contents", "Info.plist").read_bytes())
    with open(target_app.joinpath("Contents", "Info.plist"), mode="wb") as f:
        pl["CFBundleExecutable"] = "main"
        plistlib.dump(pl, f)


def create_app(app: path.PathLink, target: path.PathLink, force: bool = False):
    """根据app来构建一个新的app(target)"""
    app_path = Path(app)
    if not app_path.exists():
        fmt.error(f"Not found {app_path.as_posix()} path.")
        return False
    target_path = Path(target).expanduser()
    target_app = init_app(target_path, app_path.name, force)
    if target_app:
        create_main_by_shell(app_path, target_app)
        copy_Info(app_path, target_app)
        cmd.run(
            [
                "rsync",
                "-az",
                "--chmod=-w",
                "--copy-unsafe-links",
                "--include=*.icns",
                "--exclude=*",
                f"'{app_path.joinpath('Contents', 'Resources').as_posix()}/'",
                f"'{target_app.joinpath('Contents', 'Resources').as_posix()}/'",
            ],
            shell=True,
        )
        return True


def sync_trampolines(apps: path.PathLink, target_dir: path.PathLink):
    apps_path = Path(apps)
    if not (apps_path.exists() and apps_path.is_dir()):
        fmt.error(f"Target {apps_path.as_posix()} is not a directory")
        return False
    target_path = Path(target_dir)
    tmpDir = mkdtemp()
    is_backup = False
    if target_path.exists():
        is_backup = True
        target_path.chmod(0o755)
        cmd.getout(f"mv -vf '{target_path.as_posix()}' {tmpDir}")
    for i in apps_path.iterdir():
        if i.suffix == ".app":
            fmt.info(f"Sync trampolines {i.name} ...")
            create_app(i, target_dir, True)
    if is_backup:
        fmt.info(
            f"If you wish to retrieve the deleted app please check the table of contents {tmpDir}"
        )
    target_path.chmod(0o544)
