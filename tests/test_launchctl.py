from unittest.mock import patch, MagicMock


class TestGetAllService:
    @patch("sd.api.launchctl.cmd")
    def test_get_all_service(self, mock_cmd):
        from sd.api.launchctl import get_all_service

        mock_cmd.getout.return_value = (
            "PID\tStatus\tLabel\n123\t0\torg.nixos.test-service"
        )
        result = get_all_service()
        assert "test-service" in result


class TestGetService:
    @patch("sd.api.launchctl.get_all_service")
    def test_get_service_with_full_name(self, mock_get_all):
        from sd.api.launchctl import get_service

        result = get_service("org.nixos.test")
        assert result == "org.nixos.test"

    @patch("sd.api.launchctl.get_all_service")
    def test_get_service_with_short_name(self, mock_get_all):
        from sd.api.launchctl import get_service

        mock_get_all.return_value = ["test", "other"]
        result = get_service("test")
        assert result == "org.nixos.test"

    @patch("sd.api.launchctl.get_all_service")
    @patch("sd.api.launchctl.fmt")
    def test_get_service_not_found(self, mock_fmt, mock_get_all):
        from sd.api.launchctl import get_service

        mock_get_all.return_value = []
        result = get_service("nonexistent")
        assert result == ""


class TestGetServicePath:
    def test_get_service_path_with_org_nixos(self):
        from sd.api.launchctl import get_service_path

        result = get_service_path("org.nixos.test")
        assert "org.nixos.test.plist" in result

    def test_get_service_path_other(self):
        from sd.api.launchctl import get_service_path

        result = get_service_path("/path/to/plist")
        assert result == "/path/to/plist"


class TestLaunchctlCommands:
    @patch("sd.api.launchctl.cmd")
    @patch("sd.api.launchctl.get_service")
    def test_restart_service(self, mock_get_service, mock_cmd):
        from sd.api.launchctl import restart

        mock_get_service.return_value = "org.nixos.test"
        mock_cmd.run.return_value = MagicMock(stdout=b"123")
        restart("test", dry_run=True)

    @patch("sd.api.launchctl.cmd")
    @patch("sd.api.launchctl.get_service")
    def test_start_service(self, mock_get_service, mock_cmd):
        from sd.api.launchctl import start

        mock_get_service.return_value = "org.nixos.test"
        start("test", dry_run=True)

    @patch("sd.api.launchctl.cmd")
    @patch("sd.api.launchctl.get_service")
    def test_stop_service(self, mock_get_service, mock_cmd):
        from sd.api.launchctl import stop

        mock_get_service.return_value = "org.nixos.test"
        stop("test", dry_run=True)


class TestPyValueFunctions:
    def test_py_value_true(self):
        from sd.api.launchctl import _py_value

        result = _py_value("true")
        assert result is True

    def test_py_value_false(self):
        from sd.api.launchctl import _py_value

        result = _py_value("false")
        assert result is False

    def test_py_value_int(self):
        from sd.api.launchctl import _py_value

        result = _py_value("123")
        assert result == 123

    def test_py_value_string(self):
        from sd.api.launchctl import _py_value

        result = _py_value("test")
        assert result == "test"
