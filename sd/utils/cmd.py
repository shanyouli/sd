import subprocess
from typing import List
from sd.utils import fmt as strfmt
from sd.utils.enums import Colors
from typer import secho


def fmt(cmd_list: List[str]):
    cmd_str = " ".join(cmd_list)
    return f"> {cmd_str}"


def run(
    cmd_list: List[str],
    capture_output: bool = False,
    shell: bool = False,
    show: bool = False,
) -> subprocess.CompletedProcess[str]:
    if show:
        strfmt.info(fmt(cmd_list))
    return subprocess.run(
        (" ".join(cmd_list) if shell else cmd_list),
        capture_output=capture_output,
        shell=shell,
    )


def exists(cmd_str: str) -> bool:
    return run(["/usr/bin/env", "type", cmd_str], capture_output=True).returncode == 0


def test(cmd_list: List[str]) -> bool:
    return run(cmd_list).returncode == 0


def getout(cmd_str: str | List[str], shell: bool = False, show: bool = False) -> str:
    "获取命令结果，当结果状态码非0时，抛出错误"
    if isinstance(cmd_str, str):
        if show:
            strfmt.info(cmd_str)
        status_code, result = subprocess.getstatusoutput(cmd_str)
        if status_code == 0:
            return result
        else:
            raise subprocess.SubprocessError(result)
    else:
        process = run(cmd_str, capture_output=True, shell=shell, show=show)
        if process.returncode == 0:
            return process.stdout.decode().strip()
        else:
            raise subprocess.SubprocessError(process.stdout.decode().strip())
