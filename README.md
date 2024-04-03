# `sd`

**Usage**:

```console
$ sd [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--install-completion`: Install completion for the current shell.
* `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
* `--help`: Show this message and exit.

**Commands**:

* `bootstrap`: builds an initial configuration
* `build`: builds the specified flake output; infers...
* `cache`: cache the output environment of flake.nix
* `clean`: remove previously built configurations and...
* `disksetup`: configure disk setup for nix-darwin
* `gc`: run garbage collection on unused nix store...
* `init`: Reinitialize darwin
* `pull`: pull changes from remote repo
* `refresh`: Redirect the bundle id to specify the version
* `repl`: nix repl
* `switch`: builds and activates the specified flake...
* `update`: update all flake inputs or optionally...

## `sd bootstrap`

builds an initial configuration

**Usage**:

```console
$ sd bootstrap [OPTIONS] [HOST]
```

**Arguments**:

* `[HOST]`: the hostname of the configuration to build  [default: lyeli@aarch64-darwin]

**Options**:

* `--nixos / --no-nixos`: [default: no-nixos]
* `--darwin / --no-darwin`: [default: no-darwin]
* `--home-manager / --no-home-manager`: [default: no-home-manager]
* `--remote / --no-remote`: whether to fetch current changes from the remote  [default: no-remote]
* `--debug / --no-debug`: [default: no-debug]
* `--help`: Show this message and exit.

## `sd build`

builds the specified flake output; infers correct platform to use if not specified

**Usage**:

```console
$ sd build [OPTIONS] [HOST]
```

**Arguments**:

* `[HOST]`: the hostname of the configuration to build  [default: lyeli@aarch64-darwin]

**Options**:

* `--remote / --no-remote`: whether to fetch current changes from the remote  [default: no-remote]
* `--nixos / --no-nixos`: [default: no-nixos]
* `--darwin / --no-darwin`: [default: no-darwin]
* `--home-manager / --no-home-manager`: [default: no-home-manager]
* `--debug / --no-debug`: [default: debug]
* `--help`: Show this message and exit.

## `sd cache`

cache the output environment of flake.nix

**Usage**:

```console
$ sd cache [OPTIONS]
```

**Options**:

* `--cache-name TEXT`: [default: shanyouli]
* `--help`: Show this message and exit.

## `sd clean`

remove previously built configurations and symlinks from the current directory

**Usage**:

```console
$ sd clean [OPTIONS] [FILENAME]
```

**Arguments**:

* `[FILENAME]`: the filename to be cleaned, or '*' for all files  [default: result]

**Options**:

* `--help`: Show this message and exit.

## `sd disksetup`

configure disk setup for nix-darwin

**Usage**:

```console
$ sd disksetup [OPTIONS]
```

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

* `--help`: Show this message and exit.

## `sd refresh`

Redirect the bundle id to specify the version

**Usage**:

```console
$ sd refresh [OPTIONS]
```

**Options**:

* `--rd / --no-rd`: Reset to start the machine layout  [default: no-rd]
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
* `--help`: Show this message and exit.

## `sd switch`

builds and activates the specified flake output; infers correct platform to use if not specified

**Usage**:

```console
$ sd switch [OPTIONS] [HOST]
```

**Arguments**:

* `[HOST]`: the hostname of the configuration to build  [default: lyeli@aarch64-darwin]

**Options**:

* `--remote / --no-remote`: whether to fetch current changes from the remote  [default: no-remote]
* `--nixos / --no-nixos`: [default: no-nixos]
* `--darwin / --no-darwin`: [default: no-darwin]
* `--home-manager / --no-home-manager`: [default: no-home-manager]
* `--debug / --no-debug`: [default: no-debug]
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
* `--commit / --no-commit`: commit the updated lockfile  [default: no-commit]
* `--help`: Show this message and exit.
