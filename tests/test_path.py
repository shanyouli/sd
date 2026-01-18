import json
from pathlib import Path


class TestPathUtils:
    def test_is_exist_returns_true_for_existing_path(self, tmp_path):
        from sd.utils.path import is_exist

        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        assert is_exist(test_file) is True

    def test_is_exist_returns_false_for_nonexistent_path(self):
        from sd.utils.path import is_exist

        assert is_exist("/nonexistent/path/that/does/not/exist") is False

    def test_is_file_returns_true_for_file(self, tmp_path):
        from sd.utils.path import is_file

        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        assert is_file(test_file) is True

    def test_is_file_returns_false_for_directory(self, tmp_path):
        from sd.utils.path import is_file

        assert is_file(tmp_path) is False

    def test_is_dir_returns_true_for_directory(self, tmp_path):
        from sd.utils.path import is_dir

        assert is_dir(tmp_path) is True

    def test_is_dir_returns_false_for_file(self, tmp_path):
        from sd.utils.path import is_dir

        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        assert is_dir(test_file) is False

    def test_is_link_returns_true_for_symlink(self, tmp_path):
        from sd.utils.path import is_link

        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        link_path = tmp_path / "link.txt"
        link_path.symlink_to(test_file)
        assert is_link(link_path) is True

    def test_get_parent_returns_parent_path(self):
        from sd.utils.path import get_parent

        result = get_parent("/home/user/file.txt")
        assert result == Path("/home/user")

    def test_suffix_is_checks_extension(self):
        from sd.utils.path import suffix_is

        assert suffix_is("test.txt", "txt") is True
        assert suffix_is("test.txt", ".txt") is True
        assert suffix_is("test.txt", "md") is False

    def test_abspath_returns_absolute_path(self):
        from sd.utils.path import abspath

        result = abspath(".")
        assert Path(result).is_absolute()


class TestJsonUtils:
    def test_json_write_creates_file(self, tmp_path):
        from sd.utils.path import json_write

        test_file = tmp_path / "test.json"
        data = {"key": "value", "number": 42}
        json_write(test_file, data)

        assert test_file.exists()
        with open(test_file) as f:
            loaded = json.load(f)
        assert loaded == data

    def test_json_read_returns_dict(self, tmp_path):
        from sd.utils.path import json_read

        test_file = tmp_path / "test.json"
        data = {"key": "value"}
        with open(test_file, "w") as f:
            json.dump(data, f)

        result = json_read(test_file)
        assert result == data

    def test_json_read_returns_none_for_nonexistent_file(self):
        from sd.utils.path import json_read

        result = json_read("/nonexistent/file.json")
        assert result is None


class TestLinkUtils:
    def test_readlink_resolves_symlink(self, tmp_path):
        from sd.utils.path import readlink

        target = tmp_path / "target.txt"
        target.write_text("content")
        link = tmp_path / "link.txt"
        link.symlink_to(target)

        result = readlink(link, isLast=False)
        assert result == target

    def test_readlink_resolves_to_absolute_path(self, tmp_path):
        from sd.utils.path import readlink

        target = tmp_path / "target.txt"
        target.write_text("content")
        link = tmp_path / "link.txt"
        link.symlink_to(target)

        result = readlink(link, isLast=True)
        assert result.resolve() == target.resolve()

    def test_link_exists_returns_true_for_valid_link(self, tmp_path):
        from sd.utils.path import link_exists

        target = tmp_path / "target.txt"
        target.write_text("content")
        link = tmp_path / "link.txt"
        link.symlink_to(target)

        assert link_exists(link) is True


class TestRemoveUtils:
    def test_remove_file_deletes_file(self, tmp_path):
        from sd.utils.path import remove_file_or_link

        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        remove_file_or_link(test_file)
        assert not test_file.exists()

    def test_remove_file_deletes_symlink(self, tmp_path):
        from sd.utils.path import remove_file_or_link

        target = tmp_path / "target.txt"
        target.write_text("content")
        link = tmp_path / "link.txt"
        link.symlink_to(target)
        remove_file_or_link(link)
        assert not link.exists()
        assert target.exists()
