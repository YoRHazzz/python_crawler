import pytest
from multiprocessing import cpu_count
from crawler.config import recursive_set_dict, Config
import os
from shutil import rmtree

DEFAULT_CONFIG_DICT = {'multi': {'process_number': cpu_count(),
                                 'thread_number': cpu_count() if cpu_count() > 5 else 5,
                                 'delay': 1.0},
                       'proxy': {'proxy_url': '',
                                 'timeout': 10.0,
                                 'retry': 3}
                       }
DEFAULT_INI_PATH = "./tests/config/default.ini"
CONFIG_DIR_PATH = "./tests/config"


class TestConfig:
    @staticmethod
    def setup_method():
        if os.path.exists(CONFIG_DIR_PATH):
            rmtree(CONFIG_DIR_PATH)
        os.mkdir(CONFIG_DIR_PATH)
        Config.make_default_ini(DEFAULT_INI_PATH)

    def test_recursive_set_dict(self):
        test_dict = {'proxy': {'proxy_url': '',
                               'retry': 2},
                     }
        result = {'multi': {'process_number': cpu_count(),
                            'thread_number': cpu_count() if cpu_count() > 5 else 5,
                            'delay': 1.0},
                  'proxy': {'proxy_url': '',
                            'timeout': 10.0,
                            'retry': 2}
                  }
        recursive_set_dict(DEFAULT_CONFIG_DICT, test_dict)
        assert test_dict == result

    def test_customize_config(self):
        customize_dict = {'multi': {'process_number': cpu_count(),
                                    'thread_number': cpu_count() if cpu_count() > 5 else 5,
                                    'delay': 2.0},
                          'customize': {'use': 1,
                                        'char': 'a'}
                          }
        customize_ini_path = './tests/config/customize_config.ini'
        default_config = Config(DEFAULT_INI_PATH)
        Config(path=customize_ini_path, config_dict=customize_dict)
        customize_config = Config(path=customize_ini_path, config_dict=customize_dict)
        customize_config.list_config()
        assert customize_config.ini['multi'] != default_config.ini['multi']
        assert customize_config.ini['proxy'] == default_config.ini['proxy']
        assert customize_config.ini['customize']['use'] == '1'

    @pytest.mark.parametrize("section, option, value, expect_return",
                             [("multi", "process_number", 0, False),
                              ("multi", "process_number", 0.0, False),
                              ("multi", "process_number", 2, True),
                              ("multi", "thread_number", 0, False),
                              ("multi", "thread_number", 0.0, False),
                              ("multi", "thread_number", 2, True),
                              ("multi", "delay", -1, False),
                              ("multi", "delay", 1.0, True),
                              ("proxy", "timeout", 0, False),
                              ("proxy", "timeout", 5, True),
                              ("proxy", "retry", -1, False),
                              ("proxy", "retry", 101, False),
                              ("proxy", "retry", 'a', False),
                              ("proxy", "retry", 1, True),
                              ("proxy", "proxy_url", '127.0.0.1:65535', True),
                              ("proxy", "proxy_url", '127.0.0.1:65536', False),
                              ("proxy", "proxy_url", '255.255.255.255:65535', True),
                              ("proxy", "proxy_url", '255.255.255.256:65535', False),
                              ("proxy", "proxy_url", '', True)])
    def test_update_config_and_ini(self, section, option, value, expect_return):
        updated_config_ini_path = './tests/config/updated_config.ini'
        if os.path.exists(updated_config_ini_path):
            os.remove(updated_config_ini_path)
        config = Config(updated_config_ini_path)
        print(config.path)
        assert config.update_config_and_ini(section, option, value) is expect_return

    def test_wrong_schema(self):
        wrong_schema = {
            "type": True
        }
        try:
            Config(config_schema=wrong_schema)
        except SystemExit:
            assert True
        else:
            assert False
