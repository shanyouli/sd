from datetime import datetime
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import call, patch

import pytest


class TestGetFlake:
    @patch("sd.api.nix.common.DOTFILES", "/test/dotfiles")
    @patch("sd.api.nix.common.cmd")
    def test_get_flake_returns_dotfiles_when_exists(self, mock_cmd):
        from sd.api.nix import get_flake

        result = get_flake()
        assert result == "/test/dotfiles"

    @patch("sd.api.nix.common.DOTFILES", None)
    @patch("sd.api.nix.common.cmd")
    def test_get_flake_returns_remote_flake_when_no_local(self, mock_cmd):
        from sd.api.nix import REMOTE_FLAKE, get_flake

        mock_cmd.getout.side_effect = Exception("not a git repo")
        result = get_flake()
        assert result == REMOTE_FLAKE

    @patch("sd.api.nix.common.cmd")
    def test_get_flake_with_current_dir(self, mock_cmd):
        from sd.api.nix import get_flake

        mock_cmd.getout.return_value = "/tmp/test_project"
        with patch("os.path.isfile", return_value=True):
            result = get_flake(current_dir=True)
            assert "/test_project" in result


class TestFlakeInputs:
    @patch("sd.api.nix.common.path")
    def test_get_flake_inputs_by_lock(self, mock_path):
        from sd.api.nix import get_flake_inputs_by_lock

        mock_path.json_read.return_value = {
            "nodes": {
                "root": {
                    "inputs": {
                        "nixpkgs": {},
                        "home-manager": {},
                        "darwin": {},
                    }
                }
            }
        }
        result = get_flake_inputs_by_lock("/test/path")
        assert "nixpkgs" in result
        assert "home-manager" in result
        assert "darwin" in result


class TestFlakePlatform:
    @patch("sd.api.nix.common.cmd")
    def test_get_flake_platform_darwin(self, mock_cmd):
        from sd.api.nix import FlakeOutputs, get_flake_platform

        mock_cmd.exists.side_effect = lambda x: x == "darwin-rebuild"
        with patch("sd.api.nix.common.ISMAC", True):
            result = get_flake_platform()
            assert result == FlakeOutputs.DARWIN

    @patch("sd.api.nix.common.cmd")
    def test_get_flake_platform_nixos(self, mock_cmd):
        from sd.api.nix import FlakeOutputs, get_flake_platform

        mock_cmd.exists.side_effect = lambda x: x == "nixos-rebuild"
        result = get_flake_platform()
        assert result == FlakeOutputs.NIXOS


class TestDefaultHost:
    @patch("sd.api.nix.common.cmd")
    def test_get_default_host(self, mock_cmd):
        from sd.api.nix import SYSTEM_ARCH, SYSTEM_OS, get_default_host

        mock_cmd.getout.return_value = "testuser"
        result = get_default_host()
        assert result == f"testuser@{SYSTEM_ARCH}-{SYSTEM_OS}"


class TestGeneration:
    def test_generation_dataclass(self):
        from sd.api.nix import Generation

        gen = Generation(
            version=1,
            path=Path("/nix/var/nix/profiles/system-1-link"),
            created_at=datetime.now(),
        )
        assert gen.version == 1
        assert gen.path == Path("/nix/var/nix/profiles/system-1-link")


class TestReCompile:
    def test_get_re_compile_home(self):
        from sd.api.nix import get_re_compile

        result = get_re_compile(use_home=True)
        assert result.pattern == r"home-manager-(?P<number>\d+)-link"

    def test_get_re_compile_system(self):
        from sd.api.nix import get_re_compile

        result = get_re_compile(use_home=False)
        assert result.pattern == r"system-(?P<number>\d+)-link"


class TestFormatGeneration:
    def test_format_generation(self):
        from sd.api.nix import Generation, format_generation

        gen = Generation(
            version=5,
            path=Path("/test"),
            created_at=datetime(2024, 1, 1, 12, 0),
        )
        result = format_generation(gen)
        assert "2024-01-01" in result
        assert "version: 5" in result


class TestSelect:
    def test_select_returns_nixos(self):
        from sd.api.nix import FlakeOutputs, select

        result = select(nixos=True, darwin=False, home=False)
        assert result == FlakeOutputs.NIXOS

    def test_select_returns_darwin(self):
        from sd.api.nix import FlakeOutputs, select

        result = select(nixos=False, darwin=True, home=False)
        assert result == FlakeOutputs.DARWIN

    def test_select_returns_home_manager(self):
        from sd.api.nix import FlakeOutputs, select

        result = select(nixos=False, darwin=False, home=True)
        assert result == FlakeOutputs.HOME_MANAGER

    def test_select_raises_error_for_multiple(self):
        from sd.api.nix import select

        with pytest.raises((SystemExit, Exception)):
            select(nixos=True, darwin=True, home=False)


class TestNixVersion:
    @patch("sd.api.nix.common.cmd")
    def test_nix_version_str(self, mock_cmd):
        from sd.api.nix import nix_version_str

        mock_cmd.getout.return_value = "nix (Nix) 2.18.0"
        result = nix_version_str()
        assert result == "2.18.0"

    @patch("sd.api.nix.common.cmd")
    def test_nix_is_lix(self, mock_cmd):
        from sd.api.nix import nix_is_lix

        mock_cmd.getout.return_value = "nix (Lix) 2.90.0"
        result = nix_is_lix()
        assert result is True

    @patch("sd.api.nix.common.cmd")
    def test_nix_is_lix_false(self, mock_cmd):
        from sd.api.nix import nix_is_lix

        mock_cmd.getout.return_value = "nix (Nix) 2.18.0"
        result = nix_is_lix()
        assert result is False

    @patch("sd.api.nix.common.cmd")
    def test_nix_version_is_greater_true(self, mock_cmd):
        from sd.api.nix import nix_version_is_greater

        mock_cmd.getout.return_value = "nix (Nix) 2.20.0"
        result = nix_version_is_greater("2.18")
        assert result is True

    @patch("sd.api.nix.common.cmd")
    def test_nix_version_is_greater_false(self, mock_cmd):
        from sd.api.nix import nix_version_is_greater

        mock_cmd.getout.return_value = "nix (Nix) 2.10.0"
        result = nix_version_is_greater("2.18")
        assert result is False


class TestFlakeInputsEdgeCases:
    @patch("sd.api.nix.common.path")
    def test_get_flake_inputs_by_lock_empty_data(self, mock_path):
        from sd.api.nix import get_flake_inputs_by_lock

        mock_path.json_read.return_value = None
        with patch("sd.api.nix.common.typer"):
            with pytest.raises(Exception):
                get_flake_inputs_by_lock("/test/path")

    @patch("sd.api.nix.common.path")
    def test_get_flake_inputs_by_lock_missing_nodes(self, mock_path):
        from sd.api.nix import get_flake_inputs_by_lock

        mock_path.json_read.return_value = {}
        with patch("sd.api.nix.common.typer"):
            with pytest.raises(Exception):
                get_flake_inputs_by_lock("/test/path")


class TestFlakePlatformMore:
    @patch("sd.api.nix.common.cmd")
    def test_get_flake_platform_home_manager(self, mock_cmd):
        from sd.api.nix import FlakeOutputs, get_flake_platform

        mock_cmd.exists.return_value = False
        with patch("sd.api.nix.common.ISMAC", False):
            result = get_flake_platform()
            assert result == FlakeOutputs.HOME_MANAGER


class TestGetHmProfilesRoot:
    @patch("sd.api.nix.common.NIX_USER_PROFILES")
    @patch("sd.api.nix.common.NIX_PROFILES")
    def test_get_hm_profiles_root_user_exists(self, mock_profiles, mock_user_profiles):
        from sd.api.nix import get_hm_profiles_root

        mock_user_profiles.exists.return_value = True
        result = get_hm_profiles_root()
        assert result == mock_user_profiles

    @patch("sd.api.nix.common.NIX_USER_PROFILES")
    @patch("sd.api.nix.common.NIX_PROFILES")
    def test_get_hm_profiles_root_fallback_to_global(
        self, mock_profiles, mock_user_profiles
    ):
        from sd.api.nix import get_hm_profiles_root

        mock_user_profiles.exists.return_value = False
        result = get_hm_profiles_root()
        assert result is not None


class TestChangeWorkdir:
    @patch("sd.api.nix.common.DOTFILES", "/test/dotfiles")
    @patch("os.chdir")
    @patch("os.getcwd", return_value="/different/path")
    @patch("os.path.isdir", return_value=True)
    def test_change_workdir_decorator(self, mock_isdir, mock_getcwd, mock_chdir):
        from sd.api.nix import change_workdir

        @change_workdir
        def dummy_func():
            return "executed"

        result = dummy_func()
        assert result == "executed"

    @patch("sd.api.nix.common.DOTFILES", "/test/dotfiles")
    @patch("os.chdir")
    @patch("os.getcwd", return_value="/test/dotfiles")
    @patch("os.path.isdir", return_value=True)
    def test_change_workdir_no_change_needed(self, mock_isdir, mock_getcwd, mock_chdir):
        from sd.api.nix import change_workdir

        @change_workdir
        def dummy_func():
            return "executed"

        result = dummy_func()
        assert result == "executed"

    @patch("sd.api.nix.common.cmd")
    @patch("sd.api.nix.common.DOTFILES", "/test/dotfiles")
    @patch("os.chdir")
    @patch("os.getcwd", return_value="/different/path")
    @patch("os.path.isdir", return_value=True)
    def test_change_workdir_temporarily_restores_skip_worktree(
        self, mock_isdir, mock_getcwd, mock_chdir, mock_cmd
    ):
        from sd.api.nix import change_workdir

        mock_cmd.getout.return_value = "S flake.nix\nH flake.lock"

        @change_workdir
        def dummy_func():
            return "executed"

        result = dummy_func()

        assert result == "executed"
        assert mock_cmd.run.call_args_list == [
            call(
                [
                    "git",
                    "-C",
                    "/test/dotfiles",
                    "update-index",
                    "--no-skip-worktree",
                    "/test/dotfiles/flake.nix",
                ]
            ),
            call(
                [
                    "git",
                    "-C",
                    "/test/dotfiles",
                    "update-index",
                    "--skip-worktree",
                    "/test/dotfiles/flake.nix",
                ]
            ),
        ]

    @patch("sd.api.nix.common.cmd")
    @patch("sd.api.nix.common.DOTFILES", "/test/dotfiles")
    @patch("os.chdir")
    @patch("os.getcwd", return_value="/different/path")
    @patch("os.path.isdir", return_value=True)
    def test_change_workdir_restores_skip_worktree_on_error(
        self, mock_isdir, mock_getcwd, mock_chdir, mock_cmd
    ):
        from sd.api.nix import change_workdir

        mock_cmd.getout.return_value = "S flake.nix\nS flake.lock"

        @change_workdir
        def dummy_func():
            raise RuntimeError("boom")

        with pytest.raises(RuntimeError, match="boom"):
            dummy_func()

        assert mock_cmd.run.call_args_list == [
            call(
                [
                    "git",
                    "-C",
                    "/test/dotfiles",
                    "update-index",
                    "--no-skip-worktree",
                    "/test/dotfiles/flake.nix",
                ]
            ),
            call(
                [
                    "git",
                    "-C",
                    "/test/dotfiles",
                    "update-index",
                    "--no-skip-worktree",
                    "/test/dotfiles/flake.lock",
                ]
            ),
            call(
                [
                    "git",
                    "-C",
                    "/test/dotfiles",
                    "update-index",
                    "--skip-worktree",
                    "/test/dotfiles/flake.nix",
                ]
            ),
            call(
                [
                    "git",
                    "-C",
                    "/test/dotfiles",
                    "update-index",
                    "--skip-worktree",
                    "/test/dotfiles/flake.lock",
                ]
            ),
        ]


class TestGetGenerations:
    @patch("sd.api.nix.common.get_re_compile")
    @patch("sd.api.nix.common.get_hm_profiles_root")
    @patch("sd.api.nix.common.NIX_PROFILES")
    def test_get_generations_home_manager(
        self, mock_nix_profiles, mock_hm_profiles, mock_re_compile
    ):
        from sd.api.nix import get_generations

        mock_hm_profiles.return_value.iterdir.return_value = []
        result = get_generations(use_home=True)
        assert result == []


class TestUpdate:
    @patch("sd.api.nix.cmd")
    def test_update_triggers_nix_flake_update(self, mock_cmd):
        from sd.api.nix import update

        result = update.__wrapped__(inputs=None, commit=True, dry_run=True)

        mock_cmd.run.assert_called_once_with(
            ["nix", "flake", "update", "--commit-lock-file"],
            dry_run=True,
            shell=True,
        )
        assert result is None

    @patch("sd.api.nix.cmd")
    def test_update_accepts_specific_inputs(self, mock_cmd):
        from sd.api.nix import update

        result = update.__wrapped__(
            inputs=["nixpkgs", "home-manager"],
            commit=False,
            dry_run=True,
        )

        mock_cmd.run.assert_called_once_with(
            ["nix", "flake", "update", "nixpkgs", "home-manager"],
            dry_run=True,
            shell=True,
        )
        assert result is None


class TestNhBackend:
    def test_get_nh_namespace(self):
        from sd.api.nix import FlakeOutputs
        from sd.api.nix.nh import get_nh_namespace

        assert get_nh_namespace(FlakeOutputs.NIXOS) == "os"
        assert get_nh_namespace(FlakeOutputs.DARWIN) == "darwin"
        assert get_nh_namespace(FlakeOutputs.HOME_MANAGER) == "home"

    @patch("sd.api.nix.nh.get_flake", return_value="/dotfiles")
    @patch("sd.api.nix.nh.cmd")
    def test_build_with_nh_uses_home_configuration_flag(self, mock_cmd, mock_get_flake):
        from sd.api.nix import FlakeOutputs
        from sd.api.nix.nh import build_with_nh

        mock_cmd.run.return_value = CompletedProcess(args=[], returncode=0)

        build_with_nh(
            FlakeOutputs.HOME_MANAGER,
            "alice@host",
            debug=True,
            dry_run=False,
            extra_args=["--keep-going"],
        )

        mock_cmd.run.assert_called_once_with(
            [
                "nh",
                "home",
                "build",
                "--impure",
                "--show-trace",
                "-L",
                "--configuration",
                "alice@host",
                "/dotfiles",
                "--",
                "--keep-going",
            ],
            dry_run=False,
        )

    @patch("sd.api.nix.nh.cmd")
    def test_switch_with_nh_uses_local_darwin_hostname_flag(self, mock_cmd):
        from sd.api.nix import FlakeOutputs
        from sd.api.nix.nh import switch_with_nh

        mock_cmd.run.return_value = CompletedProcess(args=[], returncode=0)

        with patch("sd.api.nix.nh.shell_backup") as mock_shell_backup:
            with patch("sd.api.nix.nh.get_flake", return_value="/dotfiles"):
                switch_with_nh(
                    FlakeOutputs.DARWIN,
                    "macbook",
                    debug=False,
                    dry_run=True,
                    extra_args=None,
                )

        mock_shell_backup.assert_called_once()
        mock_cmd.run.assert_called_once_with(
            [
                "nh",
                "darwin",
                "switch",
                "--impure",
                "--dry",
                "--hostname",
                "macbook",
                "/dotfiles",
            ],
            dry_run=True,
        )


class TestNixBackendDryRunOutput:
    @patch("sd.api.nix.common.cmd")
    @patch("sd.api.nix.nix.cmd")
    @patch("sd.api.nix.nix.nix_diff")
    @patch("sd.api.nix.nix.get_current_generation", return_value=None)
    @patch("sd.api.nix.nix.get_flake", return_value="/dotfiles")
    def test_build_with_nix_restores_skip_worktree(
        self, mock_get_flake, mock_generation, mock_diff, mock_nix_cmd, mock_common_cmd
    ):
        from sd.api.nix import FlakeOutputs
        from sd.api.nix.nix import build_with_nix

        mock_common_cmd.getout.return_value = "S flake.nix"
        mock_nix_cmd.run.return_value = CompletedProcess(args=[], returncode=0)

        build_with_nix(
            FlakeOutputs.NIXOS,
            "server",
            debug=False,
            dry_run=False,
            extra_args=None,
        )

        assert mock_common_cmd.run.call_args_list == [
            call(
                [
                    "git",
                    "-C",
                    "/dotfiles",
                    "update-index",
                    "--no-skip-worktree",
                    "/dotfiles/flake.nix",
                ]
            ),
            call(
                [
                    "git",
                    "-C",
                    "/dotfiles",
                    "update-index",
                    "--skip-worktree",
                    "/dotfiles/flake.nix",
                ]
            ),
        ]
        mock_nix_cmd.run.assert_called_once_with(
            [
                "sudo",
                "nixos-rebuild",
                "build",
                "--flake",
                "/dotfiles#server",
                "--impure",
            ],
            dry_run=False,
        )

    @patch("sd.api.nix.common.cmd")
    @patch("sd.api.nix.nix.cmd")
    @patch("sd.api.nix.nix.get_current_generation", return_value=None)
    @patch("sd.api.nix.nix.get_flake", return_value="/dotfiles")
    def test_build_with_nix_restores_skip_worktree_on_error(
        self, mock_get_flake, mock_generation, mock_nix_cmd, mock_common_cmd
    ):
        from sd.api.nix import FlakeOutputs
        from sd.api.nix.nix import build_with_nix

        mock_common_cmd.getout.return_value = "S flake.nix"
        mock_nix_cmd.run.side_effect = RuntimeError("boom")

        with pytest.raises(RuntimeError, match="boom"):
            build_with_nix(
                FlakeOutputs.NIXOS,
                "server",
                debug=False,
                dry_run=False,
                extra_args=None,
            )

        assert mock_common_cmd.run.call_args_list == [
            call(
                [
                    "git",
                    "-C",
                    "/dotfiles",
                    "update-index",
                    "--no-skip-worktree",
                    "/dotfiles/flake.nix",
                ]
            ),
            call(
                [
                    "git",
                    "-C",
                    "/dotfiles",
                    "update-index",
                    "--skip-worktree",
                    "/dotfiles/flake.nix",
                ]
            ),
        ]
        mock_nix_cmd.run.assert_called_once_with(
            [
                "sudo",
                "nixos-rebuild",
                "build",
                "--flake",
                "/dotfiles#server",
                "--impure",
            ],
            dry_run=False,
        )

    @patch("sd.api.nix.nix.nix_diff")
    @patch("sd.api.nix.nix.get_current_generation", return_value=None)
    @patch("sd.api.nix.nix.get_flake", return_value="/dotfiles")
    def test_build_with_nix_nixos_dry_run_output(
        self, mock_get_flake, mock_generation, mock_diff, capsys
    ):
        from sd.api.nix import FlakeOutputs
        from sd.api.nix.nix import build_with_nix

        build_with_nix(
            FlakeOutputs.NIXOS,
            "server",
            debug=False,
            dry_run=True,
            extra_args=None,
        )

        captured = capsys.readouterr()
        assert (
            "> sudo nixos-rebuild build --flake /dotfiles#server --impure"
        ) in captured.out

    @patch("sd.api.nix.nix.nix_diff")
    @patch("sd.api.nix.nix.get_current_generation", return_value=None)
    @patch("sd.api.nix.nix.get_flake", return_value="/dotfiles")
    def test_build_with_nix_darwin_dry_run_output(
        self, mock_get_flake, mock_generation, mock_diff, capsys
    ):
        from sd.api.nix import FlakeOutputs
        from sd.api.nix.nix import build_with_nix

        build_with_nix(
            FlakeOutputs.DARWIN,
            "macbook",
            debug=True,
            dry_run=True,
            extra_args=["--keep-going"],
        )

        captured = capsys.readouterr()
        assert (
            "> sudo darwin-rebuild build --flake /dotfiles#macbook "
            "--impure --show-trace -L --keep-going"
        ) in captured.out

    @patch("sd.api.nix.nix.nix_diff")
    @patch("sd.api.nix.nix.get_current_generation", return_value=None)
    @patch("sd.api.nix.nix.get_flake", return_value="/dotfiles")
    def test_build_with_nix_home_dry_run_output(
        self, mock_get_flake, mock_generation, mock_diff, capsys
    ):
        from sd.api.nix import FlakeOutputs
        from sd.api.nix.nix import build_with_nix

        build_with_nix(
            FlakeOutputs.HOME_MANAGER,
            "alice@host",
            debug=False,
            dry_run=True,
            extra_args=None,
        )

        captured = capsys.readouterr()
        assert (
            "> home-manager build --flake /dotfiles#alice@host --impure"
        ) in captured.out

    @patch("sd.api.nix.nix.nix_diff")
    @patch("sd.api.nix.nix.get_current_generation", return_value=None)
    @patch("sd.api.nix.nix.get_flake", return_value="/dotfiles")
    @patch("sd.api.nix.nix.shell_backup")
    def test_switch_with_nix_darwin_local_dry_run_output(
        self, mock_shell_backup, mock_get_flake, mock_generation, mock_diff, capsys
    ):
        from sd.api.nix import FlakeOutputs
        from sd.api.nix.nix import switch_with_nix

        switch_with_nix(
            FlakeOutputs.DARWIN,
            "macbook",
            debug=False,
            dry_run=True,
            extra_args=None,
        )

        captured = capsys.readouterr()
        assert (
            "> sudo darwin-rebuild switch --flake /dotfiles#macbook --impure"
        ) in captured.out
        mock_shell_backup.assert_called_once()

    @patch("sd.api.nix.nix.nix_diff")
    @patch("sd.api.nix.nix.get_current_generation", return_value=None)
    @patch("sd.api.nix.nix.get_flake", return_value="/dotfiles")
    def test_switch_with_nix_nixos_dry_run_output(
        self, mock_get_flake, mock_generation, mock_diff, capsys
    ):
        from sd.api.nix import FlakeOutputs
        from sd.api.nix.nix import switch_with_nix

        switch_with_nix(
            FlakeOutputs.NIXOS,
            "server",
            debug=True,
            dry_run=True,
            extra_args=["--fallback"],
        )

        captured = capsys.readouterr()
        assert (
            "> sudo nixos-rebuild switch --flake /dotfiles#server "
            "--impure --show-trace -L --fallback"
        ) in captured.out

    @patch("sd.api.nix.nix.nix_diff")
    @patch("sd.api.nix.nix.get_current_generation", return_value=None)
    @patch("sd.api.nix.nix.get_flake", return_value="/dotfiles")
    def test_switch_with_nix_home_local_dry_run_output(
        self, mock_get_flake, mock_generation, mock_diff, capsys
    ):
        from sd.api.nix import FlakeOutputs
        from sd.api.nix.nix import switch_with_nix

        switch_with_nix(
            FlakeOutputs.HOME_MANAGER,
            "alice@host",
            debug=False,
            dry_run=True,
            extra_args=None,
        )

        captured = capsys.readouterr()
        assert (
            "> home-manager switch --flake /dotfiles#alice@host --impure"
        ) in captured.out

    @patch("sd.api.nix.nix.get_flake", return_value="/dotfiles")
    def test_repl_with_nix_flake_dry_run_output(self, mock_get_flake, capsys):
        from sd.api.nix.nix import repl_with_nix

        repl_with_nix(pkgs=False, unstable=False, flake=True, dry_run=True)

        captured = capsys.readouterr()
        assert "> nix --extra-experimental-features repl-flake repl /dotfiles" in (
            captured.out
        )

    def test_repl_with_nix_pkgs_dry_run_output(self, capsys):
        from sd.api.nix.nix import repl_with_nix

        repl_with_nix(pkgs=True, unstable=False, flake=False, dry_run=True)

        captured = capsys.readouterr()
        assert "> nix repl --expr 'import <nixpkgs> {}'" in captured.out

    def test_repl_with_nix_unstable_dry_run_output(self, capsys):
        from sd.api.nix.nix import repl_with_nix

        repl_with_nix(pkgs=False, unstable=True, flake=False, dry_run=True)

        captured = capsys.readouterr()
        assert "> nix repl --expr 'import <nixpkgs-unstable> {}'" in captured.out

    def test_repl_with_nix_builtins_dry_run_output(self, capsys):
        from sd.api.nix.nix import repl_with_nix

        repl_with_nix(pkgs=False, unstable=False, flake=False, dry_run=True)

        captured = capsys.readouterr()
        assert "> nix repl --expr builtins" in captured.out


class TestNhBackendDryRunOutput:
    @patch("sd.api.nix.nh.get_flake", return_value="/dotfiles")
    def test_build_with_nh_nixos_dry_run_output(self, mock_get_flake, capsys):
        from sd.api.nix import FlakeOutputs
        from sd.api.nix.nh import build_with_nh

        build_with_nh(
            FlakeOutputs.NIXOS,
            "server",
            debug=False,
            dry_run=True,
            extra_args=None,
        )

        captured = capsys.readouterr()
        assert (
            "> nh os build --impure --dry --hostname server /dotfiles"
        ) in captured.out

    @patch("sd.api.nix.nh.get_flake", return_value="/dotfiles")
    def test_build_with_nh_darwin_dry_run_output(self, mock_get_flake, capsys):
        from sd.api.nix import FlakeOutputs
        from sd.api.nix.nh import build_with_nh

        build_with_nh(
            FlakeOutputs.DARWIN,
            "macbook",
            debug=True,
            dry_run=True,
            extra_args=["--keep-going"],
        )

        captured = capsys.readouterr()
        assert (
            "> nh darwin build --impure --dry --show-trace -L "
            "--hostname macbook /dotfiles -- --keep-going"
        ) in captured.out

    @patch("sd.api.nix.nh.get_flake", return_value="/dotfiles")
    def test_build_with_nh_home_dry_run_output(self, mock_get_flake, capsys):
        from sd.api.nix import FlakeOutputs
        from sd.api.nix.nh import build_with_nh

        build_with_nh(
            FlakeOutputs.HOME_MANAGER,
            "alice@host",
            debug=False,
            dry_run=True,
            extra_args=None,
        )

        captured = capsys.readouterr()
        assert (
            "> nh home build --impure --dry --configuration alice@host /dotfiles"
        ) in captured.out

    @patch("sd.api.nix.nh.get_flake", return_value="/dotfiles")
    def test_switch_with_nh_home_dry_run_output(self, mock_get_flake, capsys):
        from sd.api.nix import FlakeOutputs
        from sd.api.nix.nh import switch_with_nh

        switch_with_nh(
            FlakeOutputs.HOME_MANAGER,
            "alice@host",
            debug=False,
            dry_run=True,
            extra_args=None,
        )

        captured = capsys.readouterr()
        assert (
            "> nh home switch --impure --dry --configuration alice@host /dotfiles"
        ) in captured.out

    @patch("sd.api.nix.nh.get_flake", return_value="/dotfiles")
    def test_switch_with_nh_nixos_dry_run_output(self, mock_get_flake, capsys):
        from sd.api.nix import FlakeOutputs
        from sd.api.nix.nh import switch_with_nh

        switch_with_nh(
            FlakeOutputs.NIXOS,
            "server",
            debug=True,
            dry_run=True,
            extra_args=["--fallback"],
        )

        captured = capsys.readouterr()
        assert (
            "> nh os switch --impure --dry --show-trace -L "
            "--hostname server /dotfiles -- --fallback"
        ) in captured.out

    @patch("sd.api.nix.nh.get_flake", return_value="/dotfiles")
    @patch("sd.api.nix.nh.shell_backup")
    def test_switch_with_nh_darwin_dry_run_output(
        self, mock_shell_backup, mock_get_flake, capsys
    ):
        from sd.api.nix import FlakeOutputs
        from sd.api.nix.nh import switch_with_nh

        switch_with_nh(
            FlakeOutputs.DARWIN,
            "macbook",
            debug=False,
            dry_run=True,
            extra_args=None,
        )

        captured = capsys.readouterr()
        assert (
            "> nh darwin switch --impure --dry --hostname macbook /dotfiles"
        ) in captured.out
        mock_shell_backup.assert_called_once()

    @patch("sd.api.nix.nh.get_flake", return_value="/dotfiles")
    def test_repl_with_nh_home_dry_run_output(self, mock_get_flake, capsys):
        from sd.api.nix import FlakeOutputs
        from sd.api.nix.nh import repl_with_nh

        repl_with_nh(FlakeOutputs.HOME_MANAGER, dry_run=True)

        captured = capsys.readouterr()
        assert "> nh home repl /dotfiles" in captured.out

    @patch("sd.api.nix.nh.get_flake", return_value="/dotfiles")
    def test_repl_with_nh_nixos_dry_run_output(self, mock_get_flake, capsys):
        from sd.api.nix import FlakeOutputs
        from sd.api.nix.nh import repl_with_nh

        repl_with_nh(FlakeOutputs.NIXOS, dry_run=True)

        captured = capsys.readouterr()
        assert "> nh os repl /dotfiles" in captured.out

    @patch("sd.api.nix.nh.get_flake", return_value="/dotfiles")
    def test_repl_with_nh_darwin_dry_run_output(self, mock_get_flake, capsys):
        from sd.api.nix import FlakeOutputs
        from sd.api.nix.nh import repl_with_nh

        repl_with_nh(FlakeOutputs.DARWIN, dry_run=True)

        captured = capsys.readouterr()
        assert "> nh darwin repl /dotfiles" in captured.out


class TestBackendDispatch:
    @patch("sd.api.nix.nix_backend.build_with_nix")
    @patch("sd.api.nix.nh_backend.build_with_nh")
    @patch("sd.api.nix.nh_backend.has_nh", return_value=True)
    def test_build_uses_nh_when_available(
        self, mock_has_nh, mock_build_with_nh, mock_build_with_nix
    ):
        from sd.api.nix import build

        build(host="host", darwin=True, dry_run=True, extra_args=None)

        mock_build_with_nh.assert_called_once()
        mock_build_with_nix.assert_not_called()

    @patch("sd.api.nix.nix_backend.build_with_nix")
    @patch("sd.api.nix.nh_backend.build_with_nh")
    @patch("sd.api.nix.nh_backend.has_nh", return_value=False)
    def test_build_uses_nix_when_nh_missing(
        self, mock_has_nh, mock_build_with_nh, mock_build_with_nix
    ):
        from sd.api.nix import build

        build(host="host", home=True, dry_run=True, extra_args=None)

        mock_build_with_nix.assert_called_once()
        mock_build_with_nh.assert_not_called()

    @patch("sd.api.nix.nix_backend.switch_with_nix")
    @patch("sd.api.nix.nh_backend.switch_with_nh")
    @patch("sd.api.nix.nh_backend.has_nh", return_value=True)
    def test_switch_uses_nh_when_available(
        self, mock_has_nh, mock_switch_with_nh, mock_switch_with_nix
    ):
        from sd.api.nix import switch

        switch(host="host", nixos=True, dry_run=True, extra_args=None)

        mock_switch_with_nh.assert_called_once()
        mock_switch_with_nix.assert_not_called()

    @patch("sd.api.nix.nix_backend.switch_with_nix")
    @patch("sd.api.nix.nh_backend.switch_with_nh")
    @patch("sd.api.nix.nh_backend.has_nh", return_value=False)
    def test_switch_uses_nix_when_nh_missing(
        self, mock_has_nh, mock_switch_with_nh, mock_switch_with_nix
    ):
        from sd.api.nix import switch

        switch(host="host", darwin=True, dry_run=True, extra_args=None)

        mock_switch_with_nix.assert_called_once()
        mock_switch_with_nh.assert_not_called()

    @patch("sd.api.nix.nix_backend.repl_with_nix")
    @patch("sd.api.nix.nh_backend.repl_with_nh")
    @patch("sd.api.nix.nh_backend.has_nh", return_value=True)
    def test_repl_uses_nh_for_flake_mode_when_available(
        self, mock_has_nh, mock_repl_with_nh, mock_repl_with_nix
    ):
        from sd.api.nix import repl

        repl(pkgs=False, unstable=False, flake=True, dry_run=True)

        mock_repl_with_nh.assert_called_once()
        mock_repl_with_nix.assert_not_called()

    @patch("sd.api.nix.nix_backend.repl_with_nix")
    @patch("sd.api.nix.nh_backend.repl_with_nh")
    @patch("sd.api.nix.nh_backend.has_nh", return_value=True)
    def test_repl_keeps_nix_for_pkgs_mode(
        self, mock_has_nh, mock_repl_with_nh, mock_repl_with_nix
    ):
        from sd.api.nix import repl

        repl(pkgs=True, unstable=False, flake=False, dry_run=True)

        mock_repl_with_nix.assert_called_once_with(True, False, False, True)
        mock_repl_with_nh.assert_not_called()
