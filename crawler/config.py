from os.path import exists
import configparser
from multiprocessing import cpu_count

default_config = {'multi': {'process_number': cpu_count(),
                            'thread_number': cpu_count(),
                            'delay': 0.0},
                  'proxy': {'proxy_url': '',
                            'timeout': 10.0,
                            'retry': 3}
                  }


class Config:
    def __init__(self, path: str = "config.ini"):
        self.path = path
        self.conf = configparser.ConfigParser()
        self.conf.read(path)
        for section in self.conf.sections():
            for key, value in self.conf[section].items():
                if value != '':
                    try:
                        value = int(value)
                    except ValueError:
                        try:
                            value = float(value)
                        except ValueError:
                            pass
                    finally:
                        default_config[section][key] = value
        self.conf.read_dict(default_config)

        if not self._config_legal():
            exit()

        with open(self.path, 'w') as config_file:
            self.conf.write(config_file)

    def _config_legal(self) -> bool:
        from jsonschema import validate, ValidationError, SchemaError
        proxy_url_pattern = '(((https?|ftp|file)\:\/\/[-A-Za-z0-9+&@#/%?=~_|!:,.;]+[-A-Za-z0-9+&@#/%=~_|])' \
                            '|((\d{1,2}|1\d\d|2[0-4]\d|25[0-5])(\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])){3})' \
                            '\:' \
                            '([0-9]|[1-9]\d{1,3}|[1-5]\d{4}|6[0-5]{2}[0-3][0-5]))' \
                            '|'
        config_schema = {
            "type": "object",
            "properties": {
                "multi": {
                    "type": "object",
                    "properties": {
                        "process_number": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 71
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
                            "pattern": proxy_url_pattern
                        },
                        "timeout": {
                            "type": "number",
                            "exclusiveMinimum": 0
                        },
                        "retry": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": 10000
                        }
                    },
                    "required": [
                        "timeout", "retry"
                    ]
                }
            },
            "required": [
                "multi", "proxy"
            ]
        }

        try:
            validate(instance=default_config, schema=config_schema)
        except ValidationError as e:
            print(e.path)
            print(e.message)
            return False
        except SchemaError as e:
            print(e)
            return False

        return True

    def get_process_number(self) -> int:
        return int(self.conf["multi"]["process_number"])

    def get_thread_number(self) -> int:
        return int(self.conf["multi"]["thread_number"])

    def get_delay(self) -> float:
        return float(self.conf["multi"]["delay"])

    def get_proxy_url(self) -> str:
        return self.conf["proxy"]["proxy_url"]

    def get_timeout(self) -> float:
        return float(self.conf["proxy"]["timeout"])

    def get_retry(self) -> int:
        return int(self.conf["proxy"]["retry"])


if __name__ == "__main__":
    config = Config()
    print("process_number", config.get_process_number())
    print("thread_number", config.get_thread_number())
    print("delay", config.get_delay())
    print("proxy_url", config.get_proxy_url())
    print("timeout", config.get_timeout())
    print("retry", config.get_retry())
