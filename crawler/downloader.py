from crawler.config import Config
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, wait, ALL_COMPLETED
from multiprocessing import Manager, Lock
import time
from crawler.url_manager import UrlManager
import requests
from requests.exceptions import ConnectTimeout, ReadTimeout, ConnectionError
from retrying import retry

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/84.0.4147.105 Safari/537.36 Edg/84.0.522.52'}


def is_retryable_request_error(exception):
    return isinstance(exception, (ConnectTimeout, ReadTimeout))


class Downloader:
    def __init__(self, config: Config):
        self.config = config

    @retry(stop_max_attempt_number=3, retry_on_exception=is_retryable_request_error)
    def get_req(self, url):
        req = requests.get(url, headers=HEADERS, timeout=float(self.config.ini["proxy"]["timeout"]))
        assert req.status_code == 200, req.status_code
        return req

    def download_thread(self, url_manager):
        url = url_manager.get_url()
        while url is not None:
            try:
                req = self.get_req(url)
            except AssertionError as e:
                print('\n', 'failed: ', url, "error:", e.args[0])
                url_manager.fail_url(url)
            except Exception as e:
                print('\n', 'failed: ', url, e.__class__)
                url_manager.fail_url(url)
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

    def get_reqs_dict(self, urls: list) -> dict:
        lock = Manager().Lock()
        url_manager = UrlManager(lock)
        url_manager.add_urls(urls)

        process_number = min(int(self.config.ini["multi"]["process_number"]), len(urls))
        thread_number = int(self.config.ini["multi"]["thread_number"])
        thread_number = min((len(urls) // thread_number) + 1, thread_number)

        process_executor = ProcessPoolExecutor(max_workers=process_number)
        process_futures = []
        for i in range(process_number):
            future = process_executor.submit(self.download_process, thread_number, url_manager)
            process_futures.append(future)
        wait(process_futures, return_when=ALL_COMPLETED)
        print("")
        return url_manager.detail_dict


if __name__ == '__main__':
    t1 = time.time()
    urls = ["http://www.google.com", "www.google.com", "http://www.hubianluanzao13123123123.com"]
    for i in range(10):
        urls.append("http://www.baidu.com")
    downloader = Downloader(Config("downloader.ini"))
    result = downloader.get_reqs_dict(urls)
    print(len(result))
    # downloader.config.list_config()
    print("total:", time.time() - t1, "second")
