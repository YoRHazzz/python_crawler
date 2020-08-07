# Python_Crawler

![PyInstaller](https://github.com/YoRHazzz/Python_Crawler/workflows/PyInstaller/badge.svg?branch=dev)
![python](https://img.shields.io/github/pipenv/locked/python-version/YoRHazzz/Python_Crawler/dev)
![CodeFactor](https://www.codefactor.io/repository/github/yorhazzz/python_crawler/badge/dev)

学习爬虫用, 多进程多线程获取url的response

# 依赖

requirements.txt

```
jsonschema
requests
bs4
lxml
tqdm
```



## 如何使用?

```python
from crawler.core import Downloader
...
downloader = Downloader()
result = downloader.get_result(urls)
for url in result.finished_urls
	req = result.urls_detail[url]
    ...
```

Downloader被实例化后, 会在当前目录生成一个默认配置文件config.ini

```ini
[multi]
process_number = 12
thread_number = 12
delay = 1.0

[proxy]
proxy_url = 
timeout = 10.0
retry = 3

```

默认配置文件参数意义如下

- process_number: 总共开多少个进程
- thread_number: 每个进程里开多少个线程
- delay: 每个线程获取一个response后的休眠时间
- proxy_url: 代理的ip地址:端口号(如 127.0.0.1:10809), 不接受url:port
- timeout: 每个url每次尝试的时限
- retry: 每个url失败后最多重试的次数

## 几个例子程序: sample

1. sample/novel_downloader.py

   从笔趣阁爬取小说, 输出如下

   ```
   请输入小说名称: 诡秘之主
   搜索到小说: 《诡秘之主》, 耗时: 0.74s
   分析章节列表完成, 耗时: 2.51s
   *************************** 下载小说 ***************************
   add urls: 100%|█████████████████████████████████████████████████████████████████| 1425/1425 [00:00<00:00, 6190.67url/s]
   download urls: 100%|████████████████████████████████████████| 1425/1425 [01:09<00:00, 20.51url/s, process=12, thread=5]
   
   initialize download tasks cost: 3.88s
   finish download task cost: 69.49s
   total cost: 73.37s
   finished: 1425|failed: 0|total: 1425
   ************************** 重试失败章节 **************************
   no failed urls
   finished: 1425|failed: 0|total: 1425
   ************************** 分离章节内容 **************************
   分离章节内容: 100%|██████████████████████████████████████████████████| 1425/1425 [00:02<00:00, 564.06章节/s, process=8]
   ************************** 小说写入文件 **************************
   小说写入完成, 总耗时: 82.58s
   小说位置:  C:\诡秘之主.txt
   press enter to exit...
   ```

2. hardworking_av_studio.py

   爬取最新种子晚于当天的勤奋的av制作商, 输出如下

   ```
   ********************** download urls ***********************
   add urls: 100%|█████████████████████████████████████████████████████████████████| 1414/1414 [00:00<00:00, 6007.72url/s]
   download urls: 100%|███████████████████████████████████████| 1414/1414 [00:18<00:00, 78.41url/s, process=12, thread=12]
   
   initialize download tasks cost: 4.14s
   finish download task cost: 18.04s
   total cost: 22.18s
   finished: 1394|failed: 20|total: 1414
   ******************** retry failed urls *********************
   add urls: 100%|█████████████████████████████████████████████████████████████████████| 20/20 [00:00<00:00, 5014.11url/s]
   download urls: 100%|███████████████████████████████████████████| 20/20 [00:00<00:00, 165.71url/s, process=12, thread=2]
   
   finished: 1394|failed: 20|total: 1414
   ********************* analyzing result *********************
   analyzing result: 100%|████████████████████████████████████████████| 1394/1394 [00:08<00:00, 166.49result/s, process=8]
   
   analysis completed... time cost 10.69s
   ************************** result **************************
   The result has been written to the current folder: C:\hardworking_av_studio.txt
   total time cost 38.97s
   press enter to exit...
   ```

## API

### Downloader

下载器, 获取response

```python
downloader = Downloader()
```

- ##### \__init__(self, *config: Config)

  - 初始化时可选传入自定义Config类

- ##### enable_chinese_transcoding(self)

- ##### disable_chinese_transcoding(self)

  - 启用/禁用获取到response后自动对中文进行转码

- ##### change_config(self, config: Config)

  - 更换config

- ##### get_req(self, url)

  - 获取url的response

- ##### get_result(self, urls: list, *url_manager: UrlManager)

  - 根据传入的的url列表下载response, 返回Result类或None

### Config

自动进行值/类型检查的配置文件

```python
config = Config()
config.ini[section][option]
```

像字典一样操作, 获取配置文件中section内option的值

**作为右值是str类型, 作为左值时右值必须是str类型, 需要按需求进行类型转换**



- ##### \__init__(self, path: str = "config.ini", config_dict=None, config_schema=None)

  - 根据config_dict生成位于path的配置文件, 由config_schema进行值的检查

  - path为.ini文件路径

  - config_dict是默认配置的内容, 如果删除.ini中某一项=后面的内容( 保留等号), Config类初始化时会被重置为默认值

  - config_schema ( jsonschema语法 ) 对值进行检查

  - ### config sample

    Config类的例子: sample/config_sample.py

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

    

- ##### list_config(self)

  - 显示config的内容

- ##### make_default_ini(path: str = "default.ini")

  - 刷新出一个名叫path的默认INI文件

- ##### update_config_and_ini(self, section: str, option: str, value)

  - 更新section下option的值

### Result

保存下载下来的有关信息

```python
result = Result(urls_detail, finished_urls, failed_urls, config, start_time, initial_time, end_time)
```

- 成员变量
  - urls_detail: key为url, value为response/exception的字典
  - finished_urls/failed_urls: 成功或失败的url列表

- retry_failed_urls(self, *config: Config)
  - 重试失败的url, 可选自定义config
- show_time_cost(self)
  - 打印时间花费
- show_urls_status(self)
  - 打印结果数目

#### UrlManager

可以跨线程/进程/主机的url管理器

```python
url_manager = UrlManager()
```

- add_url(self, url: str)
  - 添加一个url
- get_url(self)
  - 获取一个url, 该url为运行状态
- fail_url(self, url: str, e: Exception) -> bool
  - 将一个运行状态的url转为失败状态, 保存exception
- finish_url(self, url: str, req: Response) -> bool
  - 将一个运行状态的url转为成功状态, 保存response