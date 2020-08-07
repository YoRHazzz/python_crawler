from crawler.config import Config
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED
import time
from crawler.url_manager import UrlManager
import requests
from requests.exceptions import ConnectTimeout, ReadTimeout
from multiprocessing import Process, SimpleQueue
from tqdm import tqdm

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
        if len(self.failed_urls) == 0:
            print("no failed urls")
            return True
        config = config[0] if len(config) == 1 else self.config
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
                i += 1
                if i > retry:
                    raise e
            except Exception as e:
                raise e
            else:
                assert req.status_code == 200, req.status_code
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
                time.sleep(float(self.config.ini["multi"]["delay"]))
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

    def get_result(self, urls: list, *url_manger: UrlManager) -> Result:
        start_time = time.time()
        url_manager = url_manger[0] if len(url_manger) == 1 else UrlManager()
        bar = tqdm(range(len(urls)), total=len(urls), desc="add urls", unit="url")
        for url in urls:
            url_manager.add_url(url)
            bar.update(1)
        bar.close()
        # time.sleep(0.001)
        print("add urls time cost: {:.2f}s\n".format(time.time() - start_time))

        process_number = min(int(self.config.ini["multi"]["process_number"]), len(urls))
        thread_number = int(self.config.ini["multi"]["thread_number"])
        thread_number = min((len(urls) // process_number) + 1, thread_number)

        queue = SimpleQueue()
        for i in range(process_number):
            Process(target=self.download_process, args=(thread_number, url_manager, queue)).start()
        initial_time = time.time()
        for i in tqdm(range(len(urls)), total=len(urls), desc="download urls", unit="url",
                      postfix={"process": process_number, "thread": thread_number}):
            queue.get()
        print("")
        end_time = time.time()
        return Result(url_manager.detail_dict, url_manager.finished_urls, url_manager.failed_urls
                      , self.config, start_time, initial_time, end_time)
