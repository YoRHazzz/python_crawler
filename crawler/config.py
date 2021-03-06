import configparser
from multiprocessing import cpu_count
import copy

DEFAULT_CONFIG_DICT = {'multi': {'process_number': cpu_count(),
                                 'thread_number': cpu_count() if cpu_count() > 5 else 5,
                                 'delay': 1.0},
                       'proxy': {'proxy_url': '',
                                 'timeout': 10.0,
                                 'retry': 3}
                       }
PROXY_URL_PATTERN = r"(^(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])(.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])){3}" \
                    r":" \
                    r"([0-9]|[1-9]\d{1,3}|[1-5]\d{4}|6[0-5]{2}[0-3][0-5])$)" \
                    r"|^$"
DEFAULT_CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "multi": {
            "type": "object",
            "properties": {
                "process_number": {
                    "type": "integer",
                    "minimum": 1,
                },
                "thread_number": {
                    "type": "integer",
                    "minimum": 1,
                },
                "delay": {
                    "type": "number",
                    "minimum": 0,
                }
            },
            "required": [
                "process_number", "thread_number", "delay"
            ]
        },
        "proxy": {
            "type": "object",
            "properties": {
                "proxy_url": {
                    "type": "string",
                    "pattern": PROXY_URL_PATTERN
                },
                "timeout": {
                    "type": "number",
                    "exclusiveMinimum": 0
                },
                "retry": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 100
                }
            },
            "required": [
                "proxy_url", "timeout", "retry"
            ]
        }
    },
    "required": [
        "multi", "proxy"
    ]
}


def recursive_set_dict(src_dict: dict, des_dict: dict):
    for key in src_dict.keys():
        if key not in des_dict:
            des_dict[key] = src_dict[key]
        elif isinstance(src_dict[key], dict) and isinstance(des_dict[key], dict):
            recursive_set_dict(src_dict[key], des_dict[key])


class Config:
    def __init__(self, path: str = "config.ini", config_dict=None
                 , config_schema=None, use_default_config=True):
        self.path = path
        self.config_dict = copy.deepcopy(config_dict if config_dict is not None else DEFAULT_CONFIG_DICT)
        if use_default_config:
            recursive_set_dict(DEFAULT_CONFIG_DICT, self.config_dict)
        self.config_schema = copy.deepcopy(config_schema if config_schema is not None else DEFAULT_CONFIG_SCHEMA)
        if use_default_config:
            recursive_set_dict(DEFAULT_CONFIG_SCHEMA, self.config_schema)
        self.ini = configparser.ConfigParser()
        self.ini.read(path)

        if use_default_config:
            for section in self.ini.sections():
                for option in self.ini[section].keys():
                    value = self.get_config(section, option)
                    if value != '':
                        self.config_dict[section][option] = value
        self.ini.read_dict(self.config_dict)

        if not self._config_legal(self.config_dict, self.config_schema):
            exit()

        with open(self.path, 'w') as config_file:
            self.ini.write(config_file)

    @staticmethod
    def _config_legal(config_dict, config_schema) -> bool:
        from jsonschema import validate, ValidationError, SchemaError

        try:
            validate(instance=config_dict, schema=config_schema)
        except ValidationError as e:
            print(e.path)
            print(e.message)
            return False
        except SchemaError as e:
            print(e)
            return False

        return True

    def list_config(self):
        for section in self.ini.sections():
            for key, value in self.ini[section].items():
                print(key, ": ", value)

    @staticmethod
    def make_default_ini(path: str = "default.ini"):
        default_config = configparser.ConfigParser()
        default_config.read_dict(DEFAULT_CONFIG_DICT)
        print(DEFAULT_CONFIG_DICT)
        with open(path, 'w') as config_file:
            default_config.write(config_file)

    def update_config_and_ini(self, section: str, option: str, value):
        updated_config = copy.deepcopy(self.config_dict)
        updated_config[section][option] = value
        if self._config_legal(updated_config, self.config_schema):
            self.config_dict[section][option] = value
            self.ini[section][option] = str(value)
            with open(self.path, 'w') as config_file:
                self.ini.write(config_file)
            return True

        return False

    def get_config(self, section: str, option: str):
        value = self.ini[section][option]
        try:
            value = int(value)
        except ValueError:
            try:
                value = float(value)
            except ValueError:
                pass
        return value
