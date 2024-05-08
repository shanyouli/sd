import re

import typer
from sd.utils import cmd, fmt
import os

app = typer.Typer()


# @see https://github.com/andrewp-as-is/launchctl.py/raw/master/launchctl/__init__.py
def get_all_service():
    result = cmd.getout('launchctl list')
    result_list = result.split('\n')
    compile = re.compile('.*org\.nixos\.(.*)')
    return [compile.match(i).group(1) for i in result_list if compile.match(i)]


def get_all_failed_service():
    result = cmd.getout('launchctl list')
    out = []
    for i in result.split('\n'):
        if i.find('org.nixos.'):
            i_list = i.split()
            if i_list[0] == '-' and i_list[1] != '0':
                fmt.warn(
                    f'{i_list[2]} service Failure to execute returns code: {i_list[1]}'
                )
                out.append(i_list[2])
    return out


def get_service(service_name: str) -> str:
    if service_name.find('.') != -1:
        return service_name
    elif service_name in get_all_service():
        return f'org.nixos.{service_name}'
    else:
        fmt.warn(f'{service_name} service no found')
        return ''


def get_service_path(name: str) -> str:
    if name.startswith('org.nixos.'):
        return os.path.join(
            os.path.abspath(os.path.expanduser('~/Library/LaunchAgents')),
            f'{name}.plist',
        )
    else:
        return name


@app.command(help='restart <org.nixos.xxx> service')
def restart(
    service_name: str = typer.Argument('', help='service name'),
    all_service: bool = typer.Option(False, '--all', '-a', help='restart all service'),
    dry_run: bool = typer.Option(False, help='Test the command'),
):
    service_name = get_service(service_name)
    if service_name:
        uid = cmd.run(['id', '-u'], capture_output=True).stdout.decode().strip()
        cmd.run(
            ['launchctl', 'kickstart', '-k', f'gui/{uid}/{service_name}'],
            dry_run=dry_run,
        )
    elif all_service:
        uid = cmd.run(['id', '-u'], capture_output=True).stdout.decode().strip()
        for i in get_all_service():
            cmd.run(
                ['launchctl', 'kickstart', '-k', f'gui/{uid}/org.nixos.{i}'],
                dry_run=dry_run,
            )
    else:
        raise typer.Abort()


@app.command(help='start a service')
def start(
    name: str = typer.Argument('', help='service name'),
    fail_services: bool = typer.Option(
        False, '-r', '--restart', help='start fail service'
    ),
    dry_run: bool = typer.Option(False, help='Test the command'),
):
    name = get_service(name)
    if name:
        cmd.run(['launchctl', 'start', name], dry_run=dry_run)
    elif fail_services:
        for i in get_all_failed_service():
            cmd.run(['launchctl', 'start', i], dry_run=dry_run)
    else:
        raise typer.Abort()


@app.command(help='stop a service')
def stop(
    name: str = typer.Argument('', help='service name'),
    dry_run: bool = typer.Option(False, help='Test the command'),
):
    name = get_service(name)
    if name:
        cmd.run(['launchctl', 'stop', name])
    else:
        raise typer.Abort()


@app.command(help='disable service')
def disable(
    name: str = typer.Argument('', help='service name'),
    dry_run: bool = typer.Option(False, help='Test the command'),
):
    if name:
        service_name = get_service(name)
        if service_name and service_name.starswith('org.nixos'):
            uid = cmd.run(['id', '-u'], capture_output=True).stdout.decode().strip()
            cmd.run(['launchctl', 'bootout', f'gui/{uid}/name'], dry_run=dry_run)
        elif os.path.exists(os.path.expanduser(name)):
            cmd.run(['launchctl', 'unload', os.path.expanduser(name)], dry_run=dry_run)
    else:
        fmt.error('Only plist and file modes generated with nix-darwin are supported.')
        raise typer.Abort()


@app.command(help='disable service')
def enable(
    name: str = typer.Argument('', help='service name'),
    dry_run: bool = typer.Option(False, help='Test the command'),
):
    if name:
        service_name = get_service(name)
        service_path = get_service_path(service_name) if service_name else name
        if os.path.exists(service_path):
            cmd.run(['launchctl', 'load', service_path], dry_run=dry_run)
    else:
        fmt.error('Only plist and file modes generated with nix-darwin are supported.')
        raise typer.Abort()


def __parse_value(string):
    return string.split(' = ')[1].replace(';', '').replace('"', '')


def _py_value(string):
    if string in ['true', 'false']:
        return string == 'true'
    try:
        return int(string)
    except ValueError:
        return string


@app.command(help='status service info')
def status(
    name: str = typer.Argument('', help='service name'),
    dry_run: bool = typer.Option(False, help='Test the command'),
):
    name = get_service(name)
    if name:
        result = cmd.getout(f'launchctl list {name}')

        out = dict()
        for line in result.splitlines():
            if '" =' in line:
                key = line.split('"')[1]
                if ';' in line:
                    out[key] = _py_value(__parse_value(line))
            if '" =' not in line and '";' in line:
                out[key] = out.get(key, []) + [line.split('"')[1]]
        if 'PID' in out.keys():
            fmt.info(f"{out['Label']} is running, PID: {out['PID']} ...")
            fmt.term_fmt_by_dict(out, use_num=False)
        else:
            fmt.warn(
                f"{out['Label']} stop running, last exit status: {out['LastExitStatus']} ..."
            )
            fmt.term_fmt_by_dict(out, use_num=False)

    else:
        raise typer.Abort()


if __name__ == '__main__':
    app()
    # print(get_all_service())
