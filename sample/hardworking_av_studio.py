from crawler.core import Downloader, Config
from multiprocessing import Process, SimpleQueue, freeze_support, cpu_count
from bs4 import BeautifulSoup
import datetime
import os
import shutil
from tqdm import tqdm
import string
import time

HARDWORKING_CONFIG_DICT = {'multi': {'process_number': cpu_count(),
                                     'analyzing_result_process_number': int(
                                         cpu_count() // 1.5) if cpu_count() > 2 else cpu_count(),
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
HARDWORKING_CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "multi": {
            "type": "object",
            "properties": {
                "process_number": {
                    "type": "integer",
                    "minimum": 1,
                },
                "analyzing_result_process_number": {
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


class HardworkingAvStudio:
    def __init__(self):
        self.result = None
        self.mini_date = datetime.date.today()

    def screen_by_mini_date(self, urls: list, queue: SimpleQueue):
        for url in urls:
            req = self.result.get_urls_detail_dict()[url]
            soup = BeautifulSoup(req.text, features='lxml')
            soup.prettify()
            date = soup.find_all('date')
            if len(date) <= 2:
                pass
            elif str(date[1].get_text()) == '0000-00-00':
                pass
            else:
                content_date = datetime.datetime.strptime(date[1].get_text(), '%Y-%m-%d').date()
                if content_date.__gt__(self.mini_date):
                    with open("hardworking_av_studio.txt", 'a+', encoding='utf-8') as file:
                        file.write(str(url) + ' : ' + str(content_date) + '\n')
            queue.put(url)
        return True

    def start(self):
        t1 = time.time()
        downloader = Downloader(Config("hardworking_av_studio.ini", HARDWORKING_CONFIG_DICT, HARDWORKING_CONFIG_SCHEMA))
        urls = ['https://www.dmmsee.zone/studio/0']
        urls.extend(['https://www.dmmsee.zone/studio/{}{}'.format(i, word) for i in range(1, 40) for word in
                     ' ' + string.ascii_lowercase])
        urls.extend(['https://www.dmmsee.zone/studio/{}'.format(i) for i in range(40, 400)])
        print(" config ".center(shutil.get_terminal_size().columns, '*'))
        downloader.config.list_config()
        print(" download urls ".center(shutil.get_terminal_size().columns, '*'))
        self.result = downloader.get_result(urls)
        self.result.show_time_cost()
        self.result.show_urls_status()
        print(" retry failed urls ".center(shutil.get_terminal_size().columns, '*'))
        self.result.retry_failed_urls()
        self.result.show_urls_status()

        if os.path.exists("hardworking_av_studio.txt"):
            os.remove("hardworking_av_studio.txt")

        print(" analyzing result ".center(shutil.get_terminal_size().columns, '*'))
        tmp_time = time.time()
        analyzing_result_process_number = downloader.config.get_config('multi', 'analyzing_result_process_number')
        queue = SimpleQueue()
        for i in range(analyzing_result_process_number):
            Process(target=self.screen_by_mini_date,
                    args=(self.result.get_finished_urls()[i::analyzing_result_process_number]
                          , queue)).start()
        for i in tqdm(range(len(self.result.get_finished_urls())), total=len(self.result.get_finished_urls()),
                      desc="analyzing result", unit="result", postfix={"process": analyzing_result_process_number}):
            queue.get()
        print("\nanalysis completed... time cost {:.2f}s".format(time.time() - tmp_time))
        print(" result ".center(60, '*'))
        print("The result has been written to the current folder:",
              os.path.join(os.getcwd(), "hardworking_av_studio.txt"))
        print("total time cost {:.2f}s".format(time.time() - t1))
        return True


if __name__ == '__main__':
    freeze_support()
    HardworkingAvStudio().start()
    input("press enter to exit...")
