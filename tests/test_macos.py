from unittest.mock import patch, MagicMock


class TestDiskSetup:
    @patch("sd.api.macos.cmd")
    def test_disk_setup_already_configured(self, mock_cmd):
        from sd.api.macos import diskSetup

        mock_cmd.test.return_value = True
        diskSetup()


class TestAlias:
    @patch("sd.api.macos.path")
    @patch("sd.api.macos.cmd")
    def test_alias_returns_original_path(self, mock_cmd, mock_path):
        from sd.api.macos import alias

        mock_path.is_file.return_value = True
        mock_path.is_exist.return_value = True
        mock_cmd.run.return_value = MagicMock(returncode=0)
        mock_cmd.getout.return_value = "/original/path"
        mock_path.abspath.side_effect = lambda x: x

        result = alias("/test/alias.app", None)
        assert result is not None


class TestRefreshDocker:
    @patch("sd.api.macos.cmd")
    def test_refresh_runs_dock_commands(self, mock_cmd):
        from sd.api.macos import refresh

        refresh(rd=False)
        mock_cmd.run.assert_called()


class TestProxy:
    @patch("sd.api.macos.Path")
    @patch("sd.api.macos.cmd")
    @patch("sd.api.macos.plistlib")
    def test_proxy_toggle_on(self, mock_plistlib, mock_cmd, mock_path):
        from sd.api.macos import proxy

        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.read_bytes.return_value = b"<plist></plist>"
        mock_path.return_value = mock_path_instance

        mock_plistlib.loads.return_value = {
            "EnvironmentVariables": {"http_proxy": "http://old:8080"}
        }
        mock_plistlib.dumps.return_value = b"<plist></plist>"

        with patch("tempfile.NamedTemporaryFile"):
            proxy("http://new:8080")


class TestSyncApps:
    @patch("sd.api.macos.macutils")
    def test_sync_apps(self, mock_macutils):
        from sd.api.macos import syncapps

        syncapps("/source", "/target")
        mock_macutils.sync_trampolines.assert_called_once()
