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

    def get_url(self):
        self.lock.acquire()
        if len(self.waiting_urls) > 0:
            url = self.waiting_urls.pop()
            self.running_urls.append(url)
            self.lock.release()
            return url
        self.lock.release()
        return None

    def remove_running_url(self, urls: list, url: str, value):
        self.lock.acquire()
        if url in self.running_urls:
            self.running_urls.remove(url)
            urls.append(url)
            self.detail_dict[url] = value
            self.lock.release()
            return True
        self.lock.release()
        return False

    def fail_url(self, url: str, e: Exception) -> bool:
        return self.remove_running_url(self.failed_urls, url, e)

    def finish_url(self, url: str, req: Response) -> bool:
        return self.remove_running_url(self.finished_urls, url, req)
