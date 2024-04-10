import subprocess
from typing import List
from typer import secho
from sd.utils.enums import Colors

def test_cmd_exists(cmd):
    return (
        subprocess.run(["/usr/bin/env", "type", cmd], capture_output=True).returncode
        == 0
    )


def test_cmd(cmd: List[str]):
    return subprocess.run(cmd).returncode == 0

def fmt_cmd(cmd: List[str]):
    cmd_str = " ".join(cmd)
    return f"> {cmd_str}"

def run_cmd(cmd: List[str], shell: bool = False):
    secho(fmt_cmd(cmd), fg=Colors.INFO.value)
    return subprocess.run((" ".join(cmd) if shell else cmd), shell=shell)

def cmd_getout(cmd: str) -> str:
    "获取命令结果，当结果状态码非0时，抛出错误"
    status_code, result = subprocess.getstatusoutput(cmd)
    if int(status_code) == 0:
        return result
    else:
        raise subprocess.SubprocessError(result)
