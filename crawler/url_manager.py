from multiprocessing import Manager
from requests import Response


class UrlManager:
    def __init__(self):
        manager = Manager()
        self.detail_dict = manager.dict()
        self.waiting_urls = manager.list()
        self.running_urls = manager.list()
        self.finished_urls = manager.list()
        self.failed_urls = manager.list()
        self.lock = manager.RLock()

    def add_url(self, url: str):
        self.lock.acquire()
        if url in self.detail_dict:
            if url in self.failed_urls:
                self.failed_urls.remove(url)
                self.waiting_urls.append(url)
        else:
            self.waiting_urls.append(url)
            self.detail_dict.setdefault(url)
        self.lock.release()
        return True

    def add_urls(self, urls: list, status=True):
        if status is True:
            for url in urls:
                self.add_url(url)
                self.urls_status()
        else:
            for url in urls:
                self.add_url(url)

    def get_url(self, status=True):
        self.lock.acquire()
        if len(self.waiting_urls) > 0:
            url = self.waiting_urls.pop()
            self.running_urls.append(url)
            if status is True:
                self.urls_status()
            self.lock.release()
            return url
        self.lock.release()
        return None

    def remove_running_url(self, urls: list, url: str, value, status=True):
        self.lock.acquire()
        if url in self.running_urls:
            self.running_urls.remove(url)
            urls.append(url)
            if status is True:
                self.urls_status()
            self.detail_dict[url] = value
            self.lock.release()
            return True
        self.lock.release()
        return False

    def fail_url(self, url: str, e: Exception, status=True) -> bool:
        return self.remove_running_url(self.failed_urls, url, e, status)

    def finish_url(self, url: str, req: Response, status=True) -> bool:
        return self.remove_running_url(self.finished_urls, url, req, status)

    def urls_status(self):
        self.lock.acquire()
        waiting = len(self.waiting_urls)
        running = len(self.running_urls)
        finished = len(self.finished_urls)
        failed = len(self.failed_urls)
        self.lock.release()
        total = waiting + running + finished + failed

        bar = '|'.join(['waiting: ' + str(waiting),
                        'running: ' + str(running),
                        'finished: ' + str(finished),
                        'failed: ' + str(failed),
                        'total: ' + str(total)])
        print('\r' + bar + ' ' * 10, end='', flush=True)
