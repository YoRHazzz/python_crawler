# Python_Crawler

![PyInstaller](https://github.com/YoRHazzz/Python_Crawler/workflows/PyInstaller/badge.svg?branch=dev)
![python](https://img.shields.io/github/pipenv/locked/python-version/YoRHazzz/Python_Crawler/dev)
![CodeFactor](https://www.codefactor.io/repository/github/yorhazzz/python_crawler/badge/dev)

学习爬虫用

## 配置config

### 初始化

```python
from crawler.config import Config
...
config = Config(path, config_dict, config_schema)
```

根据config_dict生成位于path的配置文件, 由config_schema进行值的检查

- path为.ini文件路径
- config_dict是默认配置的内容, 如果在删除.ini中某一项=后面的内容( 保留等号), 再次执行时会被重置为默认值
- config_schema ( jsonschema语法 ) 对值进行检查

### 显示/读写某一项的值

```python
config.list_config()
```

输出config的值

```python
config.ini[section][option]
```

像字典一样操作, 获取section内option的值, 可以输出或者更改该值

### sample

sample文件夹中的config_sample.py

```python
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

```

生成的config_sample.ini如下, 其中0 <= value < 10

```ini
[sample]
value = 1

```

