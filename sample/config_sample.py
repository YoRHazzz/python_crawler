from crawler.config import Config

config_dict = {'sample': {'value': 1}
               }
config_schema = {
    "type": "object",
    "properties": {
        "sample": {
            "type": "object",
            "properties": {
                "value": {
                    "type": "integer",
                    "minimum": 0,
                    "exclusiveMaximum": 10
                }
            }
        }
    }
}
if __name__ == "__main__":
    config = Config("config_sample.ini", config_dict, config_schema)
    config.list_config()
    # value :  1
    print(config.ini["sample"]["value"])
    # 1
