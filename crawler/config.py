import configparser
from multiprocessing import cpu_count

DEFAULT_CONFIG_DICT = {'multi': {'process_number': cpu_count(),
                                 'thread_number': cpu_count(),
                                 'delay': 0.0},
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
                    "maximum": 50
                },
                "thread_number": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 50
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


class Config:
    def __init__(self, path: str = "config.ini", config_dict=None
                 , config_schema=None):
        self.path = path
        self.config_dict = config_dict if config_dict is not None else DEFAULT_CONFIG_DICT
        self.config_schema = config_schema if config_schema is not None else DEFAULT_CONFIG_SCHEMA
        self.ini = configparser.ConfigParser()
        self.ini.read(path)

        for section in self.ini.sections():
            for key, value in self.ini[section].items():
                if value != '':
                    try:
                        value = int(value)
                    except ValueError:
                        try:
                            value = float(value)
                        except ValueError:
                            pass
                    finally:
                        self.config_dict[section][key] = value
        self.ini.read_dict(self.config_dict)

        if not self._config_legal():
            exit()

        with open(self.path, 'w') as config_file:
            self.ini.write(config_file)

    def _config_legal(self) -> bool:
        from jsonschema import validate, ValidationError, SchemaError

        try:
            validate(instance=self.config_dict, schema=self.config_schema)
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


if __name__ == "__main__":
    config = Config()
    config.list_config()
