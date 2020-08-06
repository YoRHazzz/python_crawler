from crawler.config import Config
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, wait, ALL_COMPLETED
import time
from crawler.url_manager import UrlManager
import requests
from requests.exceptions import ConnectTimeout, ReadTimeout

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/84.0.4147.105 Safari/537.36 Edg/84.0.522.52'}


class Result:
    def __init__(self, urls_detail: dict, finished_urls: list, failed_urls: list
                 , config: Config, start_time, initial_time, end_time):
        self.urls_detail = urls_detail
        self.finished_urls = finished_urls
        self.failed_urls = failed_urls
        self.config = config
        self.start_time = start_time
        self.initial_time = initial_time
        self.end_time = end_time

    def retry_failed_urls(self, *config: Config):
        config = config[0] if len(config) == 1 else self.config
        retry_downloader = Downloader(config)
        result = retry_downloader.get_result(self.failed_urls)
        self.urls_detail.update(result.urls_detail)

    def show_time_cost(self):
        time_result = '\n'.join(['initialize download tasks cost: {:.2f}s'.format(self.initial_time - self.start_time),
                                 'finish download task cost: {:.2f}s'.format(self.end_time - self.initial_time),
                                 'total cost: {:.2f}s'.format(self.end_time - self.start_time)])
        print(time_result)


class Downloader:
    def __init__(self, *config: Config):
        self.config = config[0] if len(config) == 1 else Config()

    def change_config(self, config: Config):
        self.config = config

    def get_req(self, url):
        i = 0
        retry = int(self.config.ini["proxy"]["retry"])
        while i <= retry:
            try:
                req = requests.get(url, headers=HEADERS, timeout=float(self.config.ini["proxy"]["timeout"]))
            except (ConnectTimeout, ReadTimeout) as e:
                if i >= retry:
                    raise e
                else:
                    i += 1
            except Exception as e:
                raise e
            else:
                assert req.status_code == 200, req.status_code
                return req

    def download_thread(self, url_manager):
        url = url_manager.get_url()
        while url is not None:
            try:
                req = self.get_req(url)
            except AssertionError as e:
                print('\n', 'failed: ', url, "error:", e.args[0])
                url_manager.fail_url(url, e)
            except Exception as e:
                print('\n', 'failed: ', url, e.__class__)
                url_manager.fail_url(url, e)
            else:
                url_manager.finish_url(url, req)
            finally:
                time.sleep(float(self.config.ini["multi"]["delay"]))
            url = url_manager.get_url()
        return True

    def download_process(self, thread_number, url_manager):
        thread_executor = ThreadPoolExecutor(max_workers=thread_number)
        thread_futures = []
        for i in range(thread_number):
            future = thread_executor.submit(self.download_thread, url_manager)
            thread_futures.append(future)
        wait(thread_futures, return_when=ALL_COMPLETED)
        return True

    def get_result(self, urls: list, *url_manger: UrlManager) -> Result:
        start_time = time.time()
        url_manager = url_manger[0] if len(url_manger) == 1 else UrlManager()
        url_manager.add_urls(urls)

        process_number = min(int(self.config.ini["multi"]["process_number"]), len(urls))
        thread_number = int(self.config.ini["multi"]["thread_number"])
        thread_number = min((len(urls) // process_number) + 1, thread_number)

        process_executor = ProcessPoolExecutor(max_workers=process_number)
        process_futures = []
        for i in range(process_number):
            future = process_executor.submit(self.download_process, thread_number, url_manager)
            process_futures.append(future)
        initial_time = time.time()
        wait(process_futures, return_when=ALL_COMPLETED)
        print("")
        end_time = time.time()
        return Result(url_manager.detail_dict, url_manager.finished_urls, url_manager.failed_urls
                      , self.config, start_time, initial_time, end_time)
