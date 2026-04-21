from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest


class TestGetFlake:
    @patch("sd.api.nix.DOTFILES", "/test/dotfiles")
    @patch("sd.api.nix.cmd")
    def test_get_flake_returns_dotfiles_when_exists(self, mock_cmd):
        from sd.api.nix import get_flake

        result = get_flake()
        assert result == "/test/dotfiles"

    @patch("sd.api.nix.DOTFILES", None)
    @patch("sd.api.nix.cmd")
    def test_get_flake_returns_remote_flake_when_no_local(self, mock_cmd):
        from sd.api.nix import get_flake
        from sd.api.nix import REMOTE_FLAKE

        mock_cmd.getout.side_effect = Exception("not a git repo")
        result = get_flake()
        assert result == REMOTE_FLAKE

    @patch("sd.api.nix.cmd")
    def test_get_flake_with_current_dir(self, mock_cmd):
        from sd.api.nix import get_flake

        mock_cmd.getout.return_value = "/tmp/test_project"
        with patch("os.path.isfile", return_value=True):
            result = get_flake(current_dir=True)
            assert "/test_project" in result


class TestFlakeInputs:
    @patch("sd.api.nix.path")
    @patch("sd.api.nix.cmd")
    def test_get_flake_inputs_by_lock(self, mock_cmd, mock_path):
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
    @patch("sd.api.nix.cmd")
    def test_get_flake_platform_darwin(self, mock_cmd):
        from sd.api.nix import get_flake_platform, FlakeOutputs

        mock_cmd.exists.side_effect = lambda x: x == "darwin-rebuild"
        with patch("sd.api.nix.ISMAC", True):
            result = get_flake_platform()
            assert result == FlakeOutputs.DARWIN

    @patch("sd.api.nix.cmd")
    def test_get_flake_platform_nixos(self, mock_cmd):
        from sd.api.nix import get_flake_platform, FlakeOutputs

        mock_cmd.exists.side_effect = lambda x: x == "nixos-rebuild"
        result = get_flake_platform()
        assert result == FlakeOutputs.NIXOS


class TestDefaultHost:
    @patch("sd.api.nix.cmd")
    def test_get_default_host(self, mock_cmd):
        from sd.api.nix import get_default_host
        from sd.api.nix import SYSTEM_ARCH, SYSTEM_OS

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
        from sd.api.nix import format_generation, Generation

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
        from sd.api.nix import select, FlakeOutputs

        result = select(nixos=True, darwin=False, home=False)
        assert result == FlakeOutputs.NIXOS

    def test_select_returns_darwin(self):
        from sd.api.nix import select, FlakeOutputs

        result = select(nixos=False, darwin=True, home=False)
        assert result == FlakeOutputs.DARWIN

    def test_select_returns_home_manager(self):
        from sd.api.nix import select, FlakeOutputs

        result = select(nixos=False, darwin=False, home=True)
        assert result == FlakeOutputs.HOME_MANAGER

    def test_select_raises_error_for_multiple(self):
        from sd.api.nix import select

        with pytest.raises((SystemExit, Exception)):
            select(nixos=True, darwin=True, home=False)


class TestNixVersion:
    @patch("sd.api.nix.cmd")
    def test_nix_version_str(self, mock_cmd):
        from sd.api.nix import nix_version_str

        mock_cmd.getout.return_value = "nix (Nix) 2.18.0"
        result = nix_version_str()
        assert result == "2.18.0"

    @patch("sd.api.nix.cmd")
    def test_nix_is_lix(self, mock_cmd):
        from sd.api.nix import nix_is_lix

        mock_cmd.getout.return_value = "nix (Lix) 2.90.0"
        result = nix_is_lix()
        assert result is True

    @patch("sd.api.nix.cmd")
    def test_nix_is_lix_false(self, mock_cmd):
        from sd.api.nix import nix_is_lix

        mock_cmd.getout.return_value = "nix (Nix) 2.18.0"
        result = nix_is_lix()
        assert result is False

    @patch("sd.api.nix.cmd")
    def test_nix_version_is_greater_true(self, mock_cmd):
        from sd.api.nix import nix_version_is_greater

        mock_cmd.getout.return_value = "nix (Nix) 2.20.0"
        result = nix_version_is_greater("2.18")
        assert result is True

    @patch("sd.api.nix.cmd")
    def test_nix_version_is_greater_false(self, mock_cmd):
        from sd.api.nix import nix_version_is_greater

        mock_cmd.getout.return_value = "nix (Nix) 2.10.0"
        result = nix_version_is_greater("2.18")
        assert result is False


class TestFlakeInputsEdgeCases:
    @patch("sd.api.nix.path")
    def test_get_flake_inputs_by_lock_empty_data(self, mock_path):
        from sd.api.nix import get_flake_inputs_by_lock

        mock_path.json_read.return_value = None
        with patch("sd.api.nix.typer"):
            with pytest.raises(Exception):
                get_flake_inputs_by_lock("/test/path")

    @patch("sd.api.nix.path")
    def test_get_flake_inputs_by_lock_missing_nodes(self, mock_path):
        from sd.api.nix import get_flake_inputs_by_lock

        mock_path.json_read.return_value = {}
        with patch("sd.api.nix.typer"):
            with pytest.raises(Exception):
                get_flake_inputs_by_lock("/test/path")


class TestFlakePlatformMore:
    @patch("sd.api.nix.cmd")
    def test_get_flake_platform_home_manager(self, mock_cmd):
        from sd.api.nix import get_flake_platform, FlakeOutputs

        mock_cmd.exists.return_value = False
        with patch("sd.api.nix.ISMAC", False):
            result = get_flake_platform()
            assert result == FlakeOutputs.HOME_MANAGER


class TestGetHmProfilesRoot:
    @patch("sd.api.nix.NIX_USER_PROFILES")
    @patch("sd.api.nix.NIX_PROFILES")
    def test_get_hm_profiles_root_user_exists(self, mock_profiles, mock_user_profiles):
        from sd.api.nix import get_hm_profiles_root

        mock_user_profiles.exists.return_value = True
        result = get_hm_profiles_root()
        assert result == mock_user_profiles

    @patch("sd.api.nix.NIX_USER_PROFILES")
    @patch("sd.api.nix.NIX_PROFILES")
    def test_get_hm_profiles_root_fallback_to_global(
        self, mock_profiles, mock_user_profiles
    ):
        from sd.api.nix import get_hm_profiles_root

        mock_user_profiles.exists.return_value = False
        result = get_hm_profiles_root()
        assert result is not None


class TestChangeWorkdir:
    @patch("sd.api.nix.DOTFILES", "/test/dotfiles")
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

    @patch("sd.api.nix.DOTFILES", "/test/dotfiles")
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


class TestGetGenerations:
    @patch("sd.api.nix.get_re_compile")
    @patch("sd.api.nix.get_hm_profiles_root")
    @patch("sd.api.nix.NIX_PROFILES")
    def test_get_generations_home_manager(
        self, mock_nix_profiles, mock_hm_profiles, mock_re_compile
    ):
        from sd.api.nix import get_generations

        mock_hm_profiles.return_value.iterdir.return_value = []
        result = get_generations(use_home=True)
        assert result == []
