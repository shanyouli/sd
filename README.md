# `sd`

**Usage**:

```console
$ sd [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `bid`: Get macos App BundleID!
* `bootstrap`: Builds an initial Configuration
* `build`: builds the specified flake output
* `cache`: cache the output environment of flake.nix
* `clean`: remove previously built configurations and...
* `darwin`: macos Commonly used shortcut commands
* `env`: save shell environment variable
* `gc`: run garbage collection on unused nix store...
* `init`: Reinitialize darwin
* `pull`: pull changes from remote repo
* `repl`: nix repl
* `sc`: macos launchctl services manager
* `service`: macos launchctl services manager
* `switch`: builds and activates the specified flake...
* `update`: update all flake inputs or optionally...

## `sd bid`

Get macos App BundleID!

**Usage**:

```console
$ sd bid [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `db`: Display all app BundleId
* `display`: Get All App Name
* `get`: get one app bundleid

### `sd bid db`

Display all app BundleId

**Usage**:

```console
$ sd bid db [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

### `sd bid display`

Get All App Name

**Usage**:

```console
$ sd bid display [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

### `sd bid get`

get one app bundleid

**Usage**:

```console
$ sd bid get [OPTIONS] [PKG]
```

**Arguments**:

* `[PKG]`: App Path, Please run: getBundleId.py display

**Options**:

* `--help`: Show this message and exit.

## `sd bootstrap`

Builds an initial Configuration

**Usage**:

```console
$ sd bootstrap [OPTIONS] [HOST]
```

**Arguments**:

* `[HOST]`: The hostname of the configuration to build  [default: lyeli@aarch64-darwin]

**Options**:

* `--nixos / --no-nixos`: [default: no-nixos]
* `--darwin / --no-darwin`: [default: no-darwin]
* `--home / --no-home`: [default: no-home]
* `--remote / --no-remote`: Whether to fetch current changes from the remote  [default: no-remote]
* `--debug / --no-debug`: [default: no-debug]
* `--dry-run / --no-dry-run`: Test the result  [default: no-dry-run]
* `-a, --args [AGES]`: nix additional parameters
* `--help`: Show this message and exit.

## `sd build`

builds the specified flake output

**Usage**:

```console
$ sd build [OPTIONS] [HOST]
```

**Arguments**:

* `[HOST]`: the hostname to build  [default: lyeli@aarch64-darwin]

**Options**:

* `--remote / --no-remote`: whether to fetch from the remote  [default: no-remote]
* `--nixos / --no-nixos`: [default: no-nixos]
* `--darwin / --no-darwin`: [default: no-darwin]
* `--home / --no-home`: [default: no-home]
* `--debug / --no-debug`: [default: debug]
* `--dry-run / --no-dry-run`: Test the result  [default: no-dry-run]
* `-a, --args [AGES]`: nix additional parameters
* `--help`: Show this message and exit.

## `sd cache`

cache the output environment of flake.nix

**Usage**:

```console
$ sd cache [OPTIONS]
```

**Options**:

* `--cache-name TEXT`: [default: shanyouli]
* `--dry-run / --no-dry-run`: Test the result  [default: no-dry-run]
* `--help`: Show this message and exit.

## `sd clean`

remove previously built configurations and symlinks from DOTFILES

**Usage**:

```console
$ sd clean [OPTIONS] [FILENAME]
```

**Arguments**:

* `[FILENAME]`: the filename to be cleaned, or '*' for all files  [default: result]

**Options**:

* `--dry-run / --no-dry-run`: Test the result  [default: no-dry-run]
* `--help`: Show this message and exit.

## `sd darwin`

macos Commonly used shortcut commands

**Usage**:

```console
$ sd darwin [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `disksetup`: Configure disk setup for nix-darwin
* `proxy`: toggle to set proxy for...
* `refresh`: Docker restart

### `sd darwin disksetup`

Configure disk setup for nix-darwin

**Usage**:

```console
$ sd darwin disksetup [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

### `sd darwin proxy`

toggle to set proxy for org.nixos.nix-daemon.plist

**Usage**:

```console
$ sd darwin proxy [OPTIONS]
```

**Options**:

* `--url TEXT`: proxy url
* `--help`: Show this message and exit.

### `sd darwin refresh`

Docker restart

**Usage**:

```console
$ sd darwin refresh [OPTIONS]
```

**Options**:

* `--rd / --no-rd`: Redirect the bundle id to specify the version  [default: no-rd]
* `--help`: Show this message and exit.

## `sd env`

save shell environment variable

**Usage**:

```console
$ sd env [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `save`: save environment var on file!

### `sd env save`

save environment var on file!

**Usage**:

```console
$ sd env save [OPTIONS] [FILE]
```

**Arguments**:

* `[FILE]`: save file  [default: sdenv.json]

**Options**:

* `--help`: Show this message and exit.

## `sd gc`

run garbage collection on unused nix store paths

**Usage**:

```console
$ sd gc [OPTIONS]
```

**Options**:

* `-d, --delete-older-than [AGE]`: specify minimum age for deleting store paths
* `-s, --save INTEGER`: Save the last x number of builds  [default: 3]
* `--dry-run / --no-dry-run`: test the result of garbage collection  [default: no-dry-run]
* `--help`: Show this message and exit.

## `sd init`

Reinitialize darwin

**Usage**:

```console
$ sd init [OPTIONS] [HOST]
```

**Arguments**:

* `[HOST]`: the hostname of the configuration to build  [default: lyeli@aarch64-darwin]

**Options**:

* `--dry-run / --no-dry-run`: Test the result of init  [default: no-dry-run]
* `--help`: Show this message and exit.

## `sd pull`

pull changes from remote repo

**Usage**:

```console
$ sd pull [OPTIONS]
```

**Options**:

* `--dry-run / --no-dry-run`: Test the result  [default: no-dry-run]
* `--help`: Show this message and exit.

## `sd repl`

nix repl

**Usage**:

```console
$ sd repl [OPTIONS]
```

**Options**:

* `--pkgs / --no-pkgs`: import <nixpkgs>  [default: no-pkgs]
* `--flake / --no-flake`: Automatically import build flake  [default: no-flake]
* `--dry-run / --no-dry-run`: Test the result  [default: no-dry-run]
* `--help`: Show this message and exit.

## `sd sc`

macos launchctl services manager

**Usage**:

```console
$ sd sc [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `disable`: disable service
* `enable`: disable service
* `restart`: restart <org.nixos.xxx> service
* `start`: start a service
* `status`: status service info
* `stop`: stop a service

### `sd sc disable`

disable service

**Usage**:

```console
$ sd sc disable [OPTIONS] [NAME]
```

**Arguments**:

* `[NAME]`: service name

**Options**:

* `--dry-run / --no-dry-run`: Test the command  [default: no-dry-run]
* `--help`: Show this message and exit.

### `sd sc enable`

disable service

**Usage**:

```console
$ sd sc enable [OPTIONS] [NAME]
```

**Arguments**:

* `[NAME]`: service name

**Options**:

* `--dry-run / --no-dry-run`: Test the command  [default: no-dry-run]
* `--help`: Show this message and exit.

### `sd sc restart`

restart <org.nixos.xxx> service

**Usage**:

```console
$ sd sc restart [OPTIONS] [SERVICE_NAME]
```

**Arguments**:

* `[SERVICE_NAME]`: service name

**Options**:

* `-a, --all`: restart all service
* `--dry-run / --no-dry-run`: Test the command  [default: no-dry-run]
* `--help`: Show this message and exit.

### `sd sc start`

start a service

**Usage**:

```console
$ sd sc start [OPTIONS] [NAME]
```

**Arguments**:

* `[NAME]`: service name

**Options**:

* `-r, --restart`: start fail service
* `--dry-run / --no-dry-run`: Test the command  [default: no-dry-run]
* `--help`: Show this message and exit.

### `sd sc status`

status service info

**Usage**:

```console
$ sd sc status [OPTIONS] [NAME]
```

**Arguments**:

* `[NAME]`: service name

**Options**:

* `--dry-run / --no-dry-run`: Test the command  [default: no-dry-run]
* `--help`: Show this message and exit.

### `sd sc stop`

stop a service

**Usage**:

```console
$ sd sc stop [OPTIONS] [NAME]
```

**Arguments**:

* `[NAME]`: service name

**Options**:

* `--dry-run / --no-dry-run`: Test the command  [default: no-dry-run]
* `--help`: Show this message and exit.

## `sd service`

macos launchctl services manager

**Usage**:

```console
$ sd service [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `disable`: disable service
* `enable`: disable service
* `restart`: restart <org.nixos.xxx> service
* `start`: start a service
* `status`: status service info
* `stop`: stop a service

### `sd service disable`

disable service

**Usage**:

```console
$ sd service disable [OPTIONS] [NAME]
```

**Arguments**:

* `[NAME]`: service name

**Options**:

* `--dry-run / --no-dry-run`: Test the command  [default: no-dry-run]
* `--help`: Show this message and exit.

### `sd service enable`

disable service

**Usage**:

```console
$ sd service enable [OPTIONS] [NAME]
```

**Arguments**:

* `[NAME]`: service name

**Options**:

* `--dry-run / --no-dry-run`: Test the command  [default: no-dry-run]
* `--help`: Show this message and exit.

### `sd service restart`

restart <org.nixos.xxx> service

**Usage**:

```console
$ sd service restart [OPTIONS] [SERVICE_NAME]
```

**Arguments**:

* `[SERVICE_NAME]`: service name

**Options**:

* `-a, --all`: restart all service
* `--dry-run / --no-dry-run`: Test the command  [default: no-dry-run]
* `--help`: Show this message and exit.

### `sd service start`

start a service

**Usage**:

```console
$ sd service start [OPTIONS] [NAME]
```

**Arguments**:

* `[NAME]`: service name

**Options**:

* `-r, --restart`: start fail service
* `--dry-run / --no-dry-run`: Test the command  [default: no-dry-run]
* `--help`: Show this message and exit.

### `sd service status`

status service info

**Usage**:

```console
$ sd service status [OPTIONS] [NAME]
```

**Arguments**:

* `[NAME]`: service name

**Options**:

* `--dry-run / --no-dry-run`: Test the command  [default: no-dry-run]
* `--help`: Show this message and exit.

### `sd service stop`

stop a service

**Usage**:

```console
$ sd service stop [OPTIONS] [NAME]
```

**Arguments**:

* `[NAME]`: service name

**Options**:

* `--dry-run / --no-dry-run`: Test the command  [default: no-dry-run]
* `--help`: Show this message and exit.

## `sd switch`

builds and activates the specified flake output

**Usage**:

```console
$ sd switch [OPTIONS] [HOST]
```

**Arguments**:

* `[HOST]`: the hostname to build  [default: lyeli@aarch64-darwin]

**Options**:

* `--remote / --no-remote`: Whether to fetch from the remote  [default: no-remote]
* `--nixos / --no-nixos`: [default: no-nixos]
* `--darwin / --no-darwin`: [default: no-darwin]
* `--home / --no-home`: [default: no-home]
* `--debug / --no-debug`: [default: no-debug]
* `--dry-run / --no-dry-run`: Test the result  [default: no-dry-run]
* `-a, --args [AGES]`: nix additional parameters
* `--help`: Show this message and exit.

## `sd update`

update all flake inputs or optionally specific flakes

**Usage**:

```console
$ sd update [OPTIONS]
```

**Options**:

* `-f, --flake [FLAKE]`: specify an individual flake to be updated
* `-n, --no-flake [FLAKE]`: Don't update the following flake
* `-s, --stable`: Update only flake-inputs that are currently stable on the system
* `--commit / --no-commit`: commit the updated lockfile  [default: no-commit]
* `--dry-run / --no-dry-run`: Test the result  [default: no-dry-run]
* `--help`: Show this message and exit.
