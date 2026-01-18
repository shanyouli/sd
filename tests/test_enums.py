import os
from unittest.mock import patch


class TestColors:
    def test_colors_enum_values(self):
        from sd.utils.enums import Colors

        assert Colors.SUCCESS.value is not None
        assert Colors.INFO.value is not None
        assert Colors.ERROR.value is not None
        assert Colors.WARN.value is not None

    def test_flake_outputs_enum(self):
        from sd.utils.enums import FlakeOutputs

        assert FlakeOutputs.NIXOS.value == "nixosConfigurations"
        assert FlakeOutputs.DARWIN.value == "darwinConfigurations"
        assert FlakeOutputs.HOME_MANAGER.value == "homeConfigurations"


class TestDotfiles:
    @patch("os.path.isdir")
    @patch("os.path.exists")
    def test_dotfiles_finds_valid_directory(self, mock_exists, mock_isdir):
        from sd.utils.enums import Dotfiles

        with patch.dict(os.environ, {"DOTFILES": "/test/dotfiles"}):
            mock_isdir.return_value = True
            mock_exists.return_value = True
            dotfiles = Dotfiles()
            result = dotfiles.value
            assert result == os.path.realpath("/test/dotfiles")

    @patch("os.path.isdir")
    def test_dotfiles_returns_none_when_no_valid_dir(self, mock_isdir):
        from sd.utils.enums import Dotfiles

        with patch.dict(os.environ, {"DOTFILES": ""}):
            mock_isdir.return_value = False
            dotfiles = Dotfiles()
            assert dotfiles.value is None


class TestSystemInfo:
    def test_system_os_is_darwin_or_linux(self):
        from sd.utils.enums import ISMAC, ISLINUX, SYSTEM_ARCH, SYSTEM_OS

        assert SYSTEM_OS in ["darwin", "linux"]
        assert ISMAC != ISLINUX
        assert SYSTEM_ARCH in ["aarch64", "x86_64", "arm64"]

    def test_username_not_empty(self):
        from sd.utils import enums

        assert enums.USERNAME is not None

    def test_remote_flake_is_valid(self):
        from sd.utils.enums import REMOTE_FLAKE

        assert REMOTE_FLAKE.startswith("github:")
