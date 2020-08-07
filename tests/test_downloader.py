import pytest
from crawler.core import Downloader, Config, UrlManager
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
test_empty_urls = []


class TestDownloader:
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

    @pytest.mark.parametrize("test_urls, expect_failed_urls_number, expect_finished_urls_number",
                             [(test_failed_urls, 1, 0),
                              (test_finished_urls, 0, 1),
                              (test_repeated_urls, 1, 1)])
    def test_typical_urls(self, test_urls, expect_failed_urls_number, expect_finished_urls_number):
        downloader = Downloader(Config(DEFAULT_INI_PATH))
        self.fast_download(downloader)

        result = downloader.get_result(test_urls)
        result.show_time_cost()
        assert len(result.get_failed_urls()) == expect_failed_urls_number
        assert len(result.get_finished_urls()) == expect_finished_urls_number

    @pytest.mark.parametrize("test_urls, expect_failed_urls_number, expect_finished_urls_number",
                             [(test_failed_urls, 1, 0),
                              (test_finished_urls, 0, 1),
                              (test_repeated_urls, 1, 1)])
    def test_customize_url_manager(self, test_urls, expect_failed_urls_number, expect_finished_urls_number):
        url_manger = UrlManager()
        for url in test_urls:
            url_manger.add_url(url)
        downloader = Downloader(Config(DEFAULT_INI_PATH))
        self.fast_download(downloader)

        result = downloader.get_result(test_urls, url_manger)
        assert len(result.get_failed_urls()) == expect_failed_urls_number
        assert len(result.get_finished_urls()) == expect_finished_urls_number

    def test_chinese_support(self):
        test_gb2312_urls = ["https://www.biqukan.com/50_50758/"]
        downloader = Downloader(Config(DEFAULT_INI_PATH))
        downloader.enable_chinese_transcoding()
        result = downloader.get_result(test_gb2312_urls)
        downloader.disable_chinese_transcoding()
        assert len(result.get_urls_detail_dict()) == 1

    def test_get_result_empty_urls(self):
        downloader = Downloader(Config(DEFAULT_INI_PATH))
        assert downloader.get_result(test_empty_urls) is None

    def test_change_config(self):
        downloader = Downloader(Config(DEFAULT_INI_PATH))
        customize_dict = {'multi': {'process_number': 1,
                                    'thread_number': 1,
                                    'delay': 2.0},
                          'customize': {'use': 1,
                                        'char': 'a'}
                          }
        customize_ini_path = './tests/config/customize_config.ini'
        config = Config(customize_ini_path, customize_dict)
        downloader.change_config(config)
