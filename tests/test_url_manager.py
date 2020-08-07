import pytest
from crawler.core import Config, UrlManager
import os
from shutil import rmtree

DEFAULT_INI_PATH = "./tests/config/default.ini"
CONFIG_DIR_PATH = "./tests/config"

test_failed_urls = ["http://www.hubianluanzao2131231231.com"]
test_finished_urls = ["http://www.baidu.com"]
test_repeated_urls = []
for i in range(10):
    test_repeated_urls.append("http://www.baidu.com")
    test_repeated_urls.append("http://www.hubianluanzao2131231231.com")


class TestUrlManager:
    @staticmethod
    def setup_method():
        if os.path.exists(CONFIG_DIR_PATH):
            rmtree(CONFIG_DIR_PATH)
        os.mkdir(CONFIG_DIR_PATH)
        Config.make_default_ini(DEFAULT_INI_PATH)

    def test_add_failed_urls(self):
        url_manager = UrlManager()
        url_manager.add_url("test_add_failed_urls")
        url_manager.get_url()
        try:
            1 / 0
        except ZeroDivisionError as e:
            url_manager.fail_url("test_add_failed_urls", e)
        url_manager.add_url("test_add_failed_urls")
        assert len(url_manager.failed_urls) == 0
        assert len(url_manager.waiting_urls) == 1

    def test_remove_un_running_url(self):
        url_manager = UrlManager()
        url_manager.add_url("test_remove_un_running_url")
        try:
            1 / 0
        except ZeroDivisionError as e:
            assert url_manager.fail_url("test_add_failed_urls", e) is False
