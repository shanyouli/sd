import os
from unittest.mock import patch


class TestGetCacheDir:
    @patch.dict(os.environ, {"XDG_CACHE_HOME": "/custom/cache"})
    def test_get_cache_dir_uses_xdg(self):
        from sd.api.env import get_cache_dir

        result = get_cache_dir()
        assert result == "/custom/cache"

    @patch.dict(os.environ, {}, clear=True)
    def test_get_cache_dir_uses_default(self):
        from sd.api.env import get_cache_dir

        with patch("os.path.expanduser", return_value="/home/user/.cache"):
            result = get_cache_dir()
            assert ".cache" in result


class TestEnvSave:
    def test_save_function_exists(self):
        from sd.api.env import save

        assert callable(save)


class TestJsonFile:
    def test_json_file_default(self):
        from sd.api.env import JSON_FILE

        assert JSON_FILE == "sdenv.json"
