import pytest
from multiprocessing import cpu_count
from crawler.config import recursive_set_dict, Config
import os
from jsonschema import ValidationError

DEFAULT_CONFIG_DICT = {'multi': {'process_number': cpu_count(),
                                 'thread_number': cpu_count() if cpu_count() > 5 else 5,
                                 'delay': 1.0},
                       'proxy': {'proxy_url': '',
                                 'timeout': 10.0,
                                 'retry': 3}
                       }
DEFAULT_INI_PATH = "./tests/config/default.ini"


class TestConfig:
    @staticmethod
    def setup_class():
        Config.make_default_ini(DEFAULT_INI_PATH)
        print("default.ini initialized")

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
                          'customize': {'use': 1}
                          }
        customize_ini_path = './tests/config/customize_config.ini'
        default_config = Config(DEFAULT_INI_PATH)
        if os.path.exists(customize_ini_path):
            os.remove(customize_ini_path)
        customize_config = Config(path=customize_ini_path, config_dict=customize_dict)
        customize_config.list_config()
        assert customize_config.ini['multi'] != default_config.ini['multi']
        assert customize_config.ini['proxy'] == default_config.ini['proxy']
        assert customize_config.ini['customize']['use'] == '1'

    @pytest.mark.parametrize("test_value, expect_return",
                             [(0, False),
                              (2, True)])
    def test_illegal_config(self, test_value, expect_return):
        illegal_config_ini_path = './tests/config/illegal_config.ini'
        illegal_config = Config()
        assert illegal_config.update_config("multi", "process_number", test_value) is expect_return
