from unittest.mock import patch, MagicMock


class TestGetAppListByPath:
    def test_get_app_list_by_path_function_exists(self):
        from sd.api.macbid import get_app_list_by_path

        assert callable(get_app_list_by_path)


class TestGetAppListByList:
    def test_get_app_list_by_list_function_exists(self):
        from sd.api.macbid import get_app_list_by_list

        assert callable(get_app_list_by_list)


class TestGetAppBundleId:
    @patch("sd.api.macbid.cmd")
    def test_get_app_bundleid_by_appname(self, mock_cmd):
        from sd.api.macbid import get_app_bundleid_by_appname

        mock_cmd.getout.return_value = "com.example.app"
        result = get_app_bundleid_by_appname("TestApp")
        assert result == "com.example.app"

    @patch("sd.api.macbid.path")
    @patch("sd.api.macbid.cmd")
    def test_get_app_bundleid_by_info(self, mock_cmd, mock_path):
        from sd.api.macbid import get_app_bundleid_by_info

        mock_path.is_exist.return_value = True
        with patch(
            "builtins.__import__", side_effect=ModuleNotFoundError("plistlib not found")
        ):
            result = get_app_bundleid_by_info("/Test/App.app")
            assert result is None


class TestGetAppBundleIdByPath:
    @patch("sd.api.macbid.cmd")
    @patch("sd.api.macbid.path")
    def test_get_app_bundleid_by_path(self, mock_path, mock_cmd):
        from sd.api.macbid import get_app_bundleid_by_path

        mock_path.is_exist.return_value = True
        mock_cmd.getout.return_value = "com.test.app"
        mock_cmd.run.return_value = MagicMock(returncode=1)
        result = get_app_bundleid_by_path("/Applications/Test.app")
        assert result == "com.test.app"


class TestAppPath:
    def test_app_path_list(self):
        from sd.api.macbid import APP_PATH

        assert "/Applications" in APP_PATH
        assert "/System/Applications" in APP_PATH
