from unittest.mock import patch


class TestStrLen:
    def test_str_len_returns_length(self):
        from sd.utils.fmt import str_len

        assert str_len("hello") == 5
        assert str_len("") == 0

    def test_str_len_with_unicode(self):
        from sd.utils.fmt import str_len

        result = str_len("你好")
        assert result >= 2


class TestStrJust:
    def test_str_rjust_pads_left(self):
        from sd.utils.fmt import str_rjust

        result = str_rjust("hi", 5, "0")
        assert result == "000hi"

    def test_str_ljust_pads_right(self):
        from sd.utils.fmt import str_ljust

        result = str_ljust("hi", 5, "0")
        assert result == "hi000"


class TestColumns:
    @patch("os.get_terminal_size")
    def test_columns_returns_positive_integer(self, mock_terminal_size):
        from sd.utils.fmt import columns

        mock_terminal_size.return_value = type("obj", (object,), {"columns": 80})()
        result = columns()
        assert isinstance(result, int)
        assert result > 0


class TestMaxSize:
    def test_max_size_returns_max_length(self):
        from sd.utils.fmt import max_size

        lst = ["aaa", "bb", "ccccc"]
        assert max_size(lst) == 5

    def test_max_size_handles_single_item(self):
        from sd.utils.fmt import max_size

        assert max_size(["a"]) == 1


class TestStrFormatting:
    def test_str_len_with_wide_characters(self):
        from sd.utils.fmt import str_len

        result = str_len("中文")
        assert result >= 2


class TestTermFmtByList:
    @patch("os.get_terminal_size")
    def test_term_fmt_by_list_runs_without_error(self, mock_terminal_size):
        from sd.utils.fmt import term_fmt_by_list

        mock_terminal_size.return_value = type("obj", (object,), {"columns": 80})()
        term_fmt_by_list(["item1", "item2"])


class TestEchoFunctions:
    def test_info_function_exists(self):
        from sd.utils.fmt import info

        assert callable(info)

    def test_warn_function_exists(self):
        from sd.utils.fmt import warn

        assert callable(warn)

    def test_error_function_exists(self):
        from sd.utils.fmt import error

        assert callable(error)

    def test_success_function_exists(self):
        from sd.utils.fmt import success

        assert callable(success)

    def test_echo_function_exists(self):
        from sd.utils.fmt import echo

        assert callable(echo)


class TestTermFmtByDict:
    @patch("os.get_terminal_size")
    def test_term_fmt_by_dict_with_data(self, mock_terminal_size):
        from sd.utils.fmt import term_fmt_by_dict

        mock_terminal_size.return_value = type("obj", (object,), {"columns": 80})()
        term_fmt_by_dict({"key1": "value1", "key2": "value2"})

    @patch("os.get_terminal_size")
    def test_term_fmt_by_dict_with_use_num(self, mock_terminal_size):
        from sd.utils.fmt import term_fmt_by_dict

        mock_terminal_size.return_value = type("obj", (object,), {"columns": 80})()
        term_fmt_by_dict({"key1": "value1"}, use_num=True)
