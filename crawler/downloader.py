from crawler.config import Config
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED
import time
from crawler.url_manager import UrlManager
import requests
from requests.exceptions import ConnectTimeout, ReadTimeout
from multiprocessing import Process, SimpleQueue, Manager
from tqdm import tqdm
import copy

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/84.0.4147.105 Safari/537.36 Edg/84.0.522.52'}


class Result:
    def __init__(self, urls_detail: dict, finished_urls: list, failed_urls: list
                 , config: Config, start_time, initial_time, end_time):
        self.urls_detail = Manager().dict()
        self.urls_detail.update(urls_detail)
        self.finished_urls = Manager().list()
        self.finished_urls.extend(finished_urls)
        self.failed_urls = Manager().list()
        self.failed_urls.extend(failed_urls)
        self.config = copy.deepcopy(config)
        self.start_time = start_time
        self.initial_time = initial_time
        self.end_time = end_time

    def get_failed_urls(self):
        return self.failed_urls

    def get_finished_urls(self):
        return self.finished_urls

    def get_urls_detail_dict(self):
        return self.urls_detail

    def retry_failed_urls(self, *new_config: Config):
        if len(self.failed_urls) == 0:
            print("no failed urls")
            return True
        config = copy.deepcopy(new_config[0] if len(new_config) == 1 else self.config)
        if len(new_config) == 1:
            config.list_config()
        retry_downloader = Downloader(config)
        result = retry_downloader.get_result(self.failed_urls)
        self.failed_urls = result.failed_urls
        for url in result.finished_urls:
            self.finished_urls.append(url)
        self.urls_detail.update(result.urls_detail)
        return True

    def show_time_cost(self):
        time_cost = '\n'.join(['initialize download tasks cost: {:.2f}s'.format(self.initial_time - self.start_time),
                               'finish download task cost: {:.2f}s'.format(self.end_time - self.initial_time),
                               'total cost: {:.2f}s'.format(self.end_time - self.start_time)])
        print(time_cost)

    def show_urls_status(self):
        urls_status = '|'.join(['finished: ' + str(len(self.finished_urls)),
                                'failed: ' + str(len(self.failed_urls)),
                                'total: ' + str(len(self.finished_urls) + len(self.failed_urls))])
        print(urls_status)


class Downloader:
    def __init__(self, *config: Config):
        self.config = copy.deepcopy(config[0]) if len(config) == 1 else Config()
        self.chinese_support = False

    def enable_chinese_transcoding(self):
        self.chinese_support = True

    def disable_chinese_transcoding(self):
        self.chinese_support = False

    def change_config(self, config: Config):
        self.config = copy.deepcopy(config)

    def get_req(self, url):
        i = 0
        retry = self.config.get_config("proxy", "retry")
        proxy_url = self.config.get_config("proxy", "proxy_url")
        proxies = {
            'http': 'http://' + proxy_url,
            'https': 'https://' + proxy_url
        } if proxy_url != '' else None
        while i <= retry:
            try:
                req = requests.get(url, headers=HEADERS, timeout=self.config.get_config("proxy", "timeout"),
                                   proxies=proxies)
            except (ConnectTimeout, ReadTimeout, requests.exceptions.ConnectionError) as e:
                i += 1
                if i > retry:
                    raise e
            else:
                assert req.status_code == 200, req.status_code
                if self.chinese_support:
                    if req.apparent_encoding.lower() == 'gb2312' or req.apparent_encoding.lower() == 'gbk':
                        req.encoding = 'gb18030'
                return req

    def download_thread(self, url_manager, queue):
        url = url_manager.get_url()
        while url is not None:
            try:
                req = self.get_req(url)
            except (AssertionError, Exception) as e:
                url_manager.fail_url(url, e)
            else:
                url_manager.finish_url(url, req)
            finally:
                queue.put(url)
                time.sleep(self.config.get_config("multi", "delay"))
            url = url_manager.get_url()
        return True

    def download_process(self, thread_number, url_manager, queue):
        thread_executor = ThreadPoolExecutor(max_workers=thread_number)
        thread_futures = []
        for i in range(thread_number):
            future = thread_executor.submit(self.download_thread, url_manager, queue)
            thread_futures.append(future)
        wait(thread_futures, return_when=ALL_COMPLETED)
        return True

    def get_result(self, urls: list, *url_manager: UrlManager):
        if len(urls) == 0:
            print("empty url list")
            return None
        start_time = time.time()
        urls = copy.deepcopy(urls)
        url_manager = url_manager[0] if len(url_manager) == 1 else UrlManager()
        bar = tqdm(range(len(urls)), total=len(urls), desc="add urls", unit="url")
        for url in urls:
            url_manager.add_url(url)
            bar.update(1)
        bar.close()
        work_number = len(url_manager.waiting_urls)
        process_number = min(self.config.get_config("multi", "process_number"), work_number)
        thread_number = self.config.get_config("multi", "thread_number")
        thread_number = min((work_number // process_number) + 1, thread_number)

        queue = SimpleQueue()
        for i in range(process_number):
            Process(target=self.download_process, args=(thread_number, url_manager, queue)).start()
        initial_time = time.time()
        for i in tqdm(range(work_number), total=work_number, desc="download urls", unit="url",
                      postfix={"process": process_number, "thread": thread_number}):
            queue.get()
        print("")
        end_time = time.time()
        return Result(url_manager.detail_dict, url_manager.finished_urls, url_manager.failed_urls
                      , self.config, start_time, initial_time, end_time)
