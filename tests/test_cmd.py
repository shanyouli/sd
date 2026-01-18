import subprocess
from unittest.mock import patch

import pytest


class TestRun:
    @patch("subprocess.run")
    def test_run_with_list_command(self, mock_run):
        from sd.utils.cmd import run

        mock_run.return_value = subprocess.CompletedProcess(
            args=["echo", "hello"], returncode=0, stdout=b"hello"
        )
        result = run(["echo", "hello"])
        assert result is not None

    @patch("subprocess.run")
    def test_run_with_string_command(self, mock_run):
        from sd.utils.cmd import run

        mock_run.return_value = subprocess.CompletedProcess(
            args="echo hello", returncode=0, stdout=b"hello"
        )
        result = run("echo hello")
        assert result is not None

    @patch("sd.utils.cmd.strfmt")
    def test_run_with_show_flag(self, mock_strfmt):
        from sd.utils.cmd import run

        with patch("subprocess.run") as mock_subprocess:
            mock_subprocess.return_value = subprocess.CompletedProcess(
                args=["echo", "hello"], returncode=0, stdout=b"hello"
            )
            run(["echo", "hello"], show=True)
            mock_strfmt.info.assert_called()

    @patch("subprocess.run")
    def test_run_dry_run_returns_none(self, mock_run):
        from sd.utils.cmd import run

        result = run(["echo", "hello"], dry_run=True)
        assert result is None
        mock_run.assert_not_called()


class TestExists:
    @patch("sd.utils.cmd.run")
    def test_exists_returns_true_when_command_found(self, mock_run):
        from sd.utils.cmd import exists

        mock_run.return_value = subprocess.CompletedProcess(
            args=["env", "type", "ls"], returncode=0, stdout=b""
        )
        assert exists("ls") is True

    @patch("sd.utils.cmd.run")
    def test_exists_returns_false_when_command_not_found(self, mock_run):
        from sd.utils.cmd import exists

        mock_run.return_value = subprocess.CompletedProcess(
            args=["env", "type", "nonexistent"], returncode=1, stdout=b""
        )
        assert exists("nonexistent") is False


class TestTest:
    @patch("sd.utils.cmd.run")
    def test_test_returns_true_on_success(self, mock_run):
        from sd.utils.cmd import test

        mock_run.return_value = subprocess.CompletedProcess(
            args=["echo", "test"], returncode=0
        )
        assert test(["echo", "test"]) is True

    @patch("sd.utils.cmd.run")
    def test_test_returns_false_on_failure(self, mock_run):
        from sd.utils.cmd import test

        mock_run.return_value = subprocess.CompletedProcess(
            args=["false"], returncode=1
        )
        assert test(["false"]) is False


class TestGetout:
    @patch("subprocess.getstatusoutput")
    def test_getout_returns_output_on_success(self, mock_getstatusoutput):
        from sd.utils.cmd import getout

        mock_getstatusoutput.return_value = (0, "output")
        result = getout("echo test")
        assert result == "output"

    @patch("subprocess.getstatusoutput")
    def test_getout_raises_error_on_failure(self, mock_getstatusoutput):
        from sd.utils.cmd import getout

        mock_getstatusoutput.return_value = (1, "error message")
        with pytest.raises(subprocess.SubprocessError):
            getout("false")

    @patch("sd.utils.cmd.run")
    def test_getout_with_list_and_failure(self, mock_run):
        from sd.utils.cmd import getout

        mock_run.return_value = subprocess.CompletedProcess(
            args=["false"], returncode=1, stdout=b"error"
        )
        with pytest.raises(subprocess.SubprocessError):
            getout(["false"])


class TestGetLatestTag:
    @patch("sd.utils.cmd.getout")
    def test_get_latest_tag_returns_tag(self, mock_getout):
        from sd.utils.cmd import get_latest_tag_by_git

        mock_getout.return_value = (
            "abc123\trefs/tags/v1.0.0^{}\nabc124\trefs/tags/v1.0.1\n"
        )
        result = get_latest_tag_by_git("github:test/repo")
        assert result == "v1.0.1"

    @patch("sd.utils.cmd.getout")
    def test_get_latest_tag_returns_none_on_error(self, mock_getout):
        from sd.utils.cmd import get_latest_tag_by_git

        mock_getout.side_effect = subprocess.CalledProcessError(1, "git")
        result = get_latest_tag_by_git("github:test/repo")
        assert result is None
