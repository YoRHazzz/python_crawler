from multiprocessing import Manager, Lock
from requests import Response


class UrlManager:
    def __init__(self, lock: Lock):
        manager = Manager()
        self.detail_dict = manager.dict()
        self.waiting_urls = manager.list()
        self.running_urls = manager.list()
        self.finished_urls = manager.list()
        self.failed_urls = manager.list()
        self.lock = lock

    def add_url(self, url: str):
        if url in self.detail_dict:
            if url in self.failed_urls:
                self.lock.acquire()
                self.failed_urls.remove(url)
                self.waiting_urls.append(url)
                self.lock.release()
        else:
            self.lock.acquire()
            self.waiting_urls.append(url)
            self.detail_dict.setdefault(url)
            self.lock.release()

    def add_urls(self, urls: list, status=True):
        if status is True:
            for url in urls:
                self.add_url(url)
                self.urls_status()
        else:
            for url in urls:
                self.add_url(url)

    def get_url(self, status=True):
        if len(self.waiting_urls) > 0:
            self.lock.acquire()
            url = self.waiting_urls.pop()
            self.running_urls.append(url)
            self.lock.release()
            if status is True:
                self.urls_status()
            return url
        else:
            return None

    def fail_url(self, url: str, status=True) -> bool:
        if url in self.running_urls:
            self.lock.acquire()
            self.running_urls.remove(url)
            self.failed_urls.append(url)
            self.lock.release()
            if status is True:
                self.urls_status()
            return True
        else:
            return False

    def finish_url(self, url: str, req: Response, status=True) -> bool:
        if url in self.running_urls:
            self.lock.acquire()
            self.running_urls.remove(url)
            self.finished_urls.append(url)
            self.lock.release()
            if status is True:
                self.urls_status()
            self.detail_dict[url] = req
            return True
        else:
            return False

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
