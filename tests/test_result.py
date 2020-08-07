import pytest
from crawler.core import Downloader, Config, UrlManager
import os
from shutil import rmtree

DEFAULT_INI_PATH = "./tests/config/default.ini"
CONFIG_DIR_PATH = "./tests/config"

test_failed_urls = ["http://www.google.com"]
test_finished_urls = ["http://www.baidu.com"]
test_repeated_urls = []
for i in range(10):
    test_repeated_urls.append("http://www.baidu.com")
    test_repeated_urls.append("http://www.hubianluanzao2131231231.com")


class TestResult:
    @staticmethod
    def setup_method():
        if os.path.exists(CONFIG_DIR_PATH):
            rmtree(CONFIG_DIR_PATH)
        os.mkdir(CONFIG_DIR_PATH)
        Config.make_default_ini(DEFAULT_INI_PATH)

    @staticmethod
    def fast_download(downloader: Downloader):
        downloader.config.ini['multi']['delay'] = '0'
        downloader.config.ini['proxy']['timeout'] = '3'
        downloader.config.ini['proxy']['retry'] = '1'

    def test_retry_failed_urls(self):
        url_manger = UrlManager()
        downloader = Downloader(Config(DEFAULT_INI_PATH))
        self.fast_download(downloader)

        result = downloader.get_result(test_repeated_urls, url_manger)
        assert len(result.failed_urls) == 1
        assert len(result.finished_urls) == 1
        result.retry_failed_urls()
        assert len(result.failed_urls) == 1
        assert len(result.finished_urls) == 1
        result = downloader.get_result(test_finished_urls)
        result.retry_failed_urls()
        result.show_urls_status()
        assert len(result.failed_urls) == 0
        assert len(result.finished_urls) == 1
        downloader.config.update_config_and_ini('proxy', 'proxy_url', '255.255.255.255:65535')
        downloader.config.make_default_ini(DEFAULT_INI_PATH)
        result = downloader.get_result(test_finished_urls)
        assert len(result.failed_urls) == 1
        assert len(result.finished_urls) == 0
        result.retry_failed_urls(Config(DEFAULT_INI_PATH))
        result.show_urls_status()
        assert len(result.failed_urls) == 0
        assert len(result.finished_urls) == 1
