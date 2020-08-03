from crawler.config import Config
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, wait, ALL_COMPLETED
import time
from crawler.url_manager import UrlManager
import requests
from requests.exceptions import ConnectTimeout, ReadTimeout, ConnectionError

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/68.0.3440.106 Safari/537.36'}


class Downloader:
    def __init__(self, config: Config):
        self.config = config
        self.url_manager = UrlManager()

    def get_req(self, url):
        i = 0
        while i < int(self.config.ini["proxy"]["retry"]):
            try:
                req = requests.get(url, headers=HEADERS, timeout=float(self.config.ini["proxy"]["timeout"]))
                return req
            except (ConnectTimeout, ReadTimeout, ConnectionError):
                print('\n', 'retry: ', url)
            except Exception as e:
                print(repr(e))
                return None
        return None

    def download_thread(self):
        url = self.url_manager.get_url()
        self.url_manager.urls_status()
        while url is not None:
            req = self.get_req(url)
            if req is not None:
                self.url_manager.url_finish(url, req)
            else:
                self.url_manager.fail_url(url)
                print('\n', 'failed: ', url)
            self.url_manager.urls_status()
            # time.sleep(float(self.config.ini["multi"]["delay"]))
            url = self.url_manager.get_url()
            self.url_manager.urls_status()
        return True

    def download_process(self, thread_number):
        thread_executor = ThreadPoolExecutor(max_workers=thread_number)
        thread_futures = []
        for i in range(thread_number):
            future = thread_executor.submit(self.download_thread)
            thread_futures.append(future)
        wait(thread_futures, return_when=ALL_COMPLETED)
        return True

    def start(self, urls: list):
        work_number = len(urls)
        self.url_manager.add_urls(urls)

        process_number = min(int(self.config.ini["multi"]["process_number"]), work_number)
        thread_number = int(self.config.ini["multi"]["thread_number"])
        thread_number = min((work_number // thread_number) + 1, thread_number)

        process_executor = ProcessPoolExecutor(max_workers=process_number)
        process_futures = []
        for i in range(process_number):
            future = process_executor.submit(self.download_process, thread_number)
            process_futures.append(future)

        wait(process_futures, return_when=ALL_COMPLETED)
        print("")
        return True

    def result(self):
        return self.url_manager.detail_dict


if __name__ == '__main__':
    t1 = time.time()
    urls = ['https://movie.douban.com/top250?start={}&filter='.format(i) for i in range(0, 226, 1)]
    downloader = Downloader(Config("downloader.ini"))
    downloader.start(urls)
    result = downloader.result()
    print(len(result))
    # downloader.config.list_config()
    print("total:", time.time() - t1, "second")
