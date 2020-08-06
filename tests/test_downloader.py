import pytest
from crawler.core import Downloader, Config
from crawler.url_manager import UrlManager
import os
from shutil import rmtree

DEFAULT_INI_PATH = "./tests/config/default.ini"
CONFIG_DIR_PATH = "./tests/config"

test_failed_urls = ["http://www.google.com"]
test_finished_urls = ["http://www.baidu.com"]
test_repeated_urls = []
for i in range(10):
    test_repeated_urls.append("http://www.baidu.com")
    test_repeated_urls.append("http://www.google.com")


class TestDownloader:
    @staticmethod
    def setup_class():
        if os.path.exists(CONFIG_DIR_PATH):
            rmtree(CONFIG_DIR_PATH)
        os.mkdir(CONFIG_DIR_PATH)
        Config.make_default_ini(DEFAULT_INI_PATH)
        print("default.ini initialized")

    @staticmethod
    def fast_download(downloader: Downloader):
        downloader.config.ini['multi']['delay'] = '0'
        downloader.config.ini['proxy']['timeout'] = '3'
        downloader.config.ini['proxy']['retry'] = '1'

    @pytest.mark.parametrize("test_urls, expect_failed_urls_number, expect_finished_urls_number",
                             [(test_failed_urls, 1, 0),
                              (test_finished_urls, 0, 1),
                              (test_repeated_urls, 1, 1)])
    def test_typical_urls(self, test_urls, expect_failed_urls_number, expect_finished_urls_number):
        downloader = Downloader(Config(DEFAULT_INI_PATH))
        self.fast_download(downloader)

        result = downloader.get_result(test_urls)
        result.show_time_cost()
        assert len(result.failed_urls) == expect_failed_urls_number
        assert len(result.finished_urls) == expect_finished_urls_number

    @pytest.mark.parametrize("test_urls, expect_failed_urls_number, expect_finished_urls_number",
                             [(test_failed_urls, 1, 0),
                              (test_finished_urls, 0, 1),
                              (test_repeated_urls, 1, 1)])
    def test_customize_url_manager(self, test_urls, expect_failed_urls_number, expect_finished_urls_number):
        url_manger = UrlManager()
        url_manger.add_urls(test_urls)
        downloader = Downloader(Config(DEFAULT_INI_PATH))
        self.fast_download(downloader)

        result = downloader.get_result(test_urls, url_manger)
        assert len(result.failed_urls) == expect_failed_urls_number
        assert len(result.finished_urls) == expect_finished_urls_number

    def test_result_retry_failed_urls(self):
        url_manger = UrlManager()
        downloader = Downloader(Config(DEFAULT_INI_PATH))
        self.fast_download(downloader)

        result = downloader.get_result(test_repeated_urls, url_manger)
        assert len(result.failed_urls) == 1
        assert len(result.finished_urls) == 1
        result.retry_failed_urls()
        assert len(result.failed_urls) == 1
        assert len(result.finished_urls) == 1
