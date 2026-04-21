from unittest.mock import patch, MagicMock


class TestInitApp:
    def test_init_app_creates_directory(self, tmp_path):
        from sd.utils.macutils import init_app

        target_path = tmp_path / "TestApp.app"
        result = init_app(target_path, "TestApp")
        assert result is not None
        assert target_path.exists()

    def test_init_app_exists_no_force(self, tmp_path):
        from sd.utils.macutils import init_app

        target_path = tmp_path / "TestApp.app"
        target_path.mkdir()
        result = init_app(target_path, "TestApp", force=False)
        assert result is False


class TestCreateMainByShell:
    def test_create_main_by_shell(self, tmp_path):
        from sd.utils.macutils import create_main_by_shell

        app_path = tmp_path / "Original.app"
        target_app = tmp_path / "Target.app"
        target_app.mkdir()
        target_app.joinpath("Contents").mkdir()
        target_app.joinpath("Contents", "MacOS").mkdir()

        create_main_by_shell(app_path, target_app)
        script = target_app.joinpath("Contents", "MacOS", "main")
        assert script.exists()


class TestCopyInfo:
    @patch("sd.utils.macutils.plistlib")
    def test_copy_info(self, mock_plistlib, tmp_path):
        from sd.utils.macutils import copy_Info

        app = tmp_path / "Source.app"
        target_app = tmp_path / "Target.app"

        app.mkdir(parents=True)
        target_app.mkdir(parents=True)
        app.joinpath("Contents").mkdir()
        target_app.joinpath("Contents").mkdir()

        info_plist = app.joinpath("Contents", "Info.plist")
        info_plist.write_bytes(
            b'<?xml version="1.0" ?><plist><dict><key>CFBundleName</key><string>Test</string></dict></plist>'
        )

        mock_plistlib.loads.return_value = {"CFBundleName": "Test"}
        mock_plistlib.dump = MagicMock()

        copy_Info(app, target_app)
        mock_plistlib.dump.assert_called_once()


class TestCreateApp:
    @patch("sd.utils.macutils.init_app")
    @patch("sd.utils.macutils.create_main_by_shell")
    @patch("sd.utils.macutils.copy_Info")
    @patch("sd.utils.macutils.cmd")
    def test_create_app_success(
        self, mock_cmd, mock_copy, mock_shell, mock_init, tmp_path
    ):
        from sd.utils.macutils import create_app

        app_path = tmp_path / "Source.app"
        app_path.mkdir()
        target_path = tmp_path / "Target"

        mock_init.return_value = target_path

        result = create_app(app_path, target_path, force=True)
        assert result is True


class TestSyncTrampolines:
    @patch("sd.utils.macutils.mkdtemp")
    @patch("sd.utils.macutils.create_app")
    @patch("sd.utils.macutils.cmd")
    @patch("sd.utils.macutils.fmt")
    def test_sync_trampolines(
        self, mock_fmt, mock_cmd, mock_create, mock_mkdtemp, tmp_path
    ):
        from sd.utils.macutils import sync_trampolines

        apps_path = tmp_path / "Apps"
        apps_path.mkdir()
        target_dir = tmp_path / "Target"
        target_dir.mkdir()

        app = apps_path / "TestApp.app"
        app.mkdir()

        mock_mkdtemp.return_value = "/tmp/test"

        sync_trampolines(apps_path, target_dir)
        mock_create.assert_called()

    @patch("sd.utils.macutils.fmt")
    def test_sync_trampolines_invalid_dir(self, mock_fmt):
        from sd.utils.macutils import sync_trampolines

        result = sync_trampolines("/nonexistent", "/target")
        assert result is False
