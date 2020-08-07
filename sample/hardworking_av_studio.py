from crawler.core import Downloader, Config
from multiprocessing import Process, SimpleQueue, freeze_support
from bs4 import BeautifulSoup
import datetime
import os
from tqdm import tqdm
import string
import time


class HardworkingAvStudio:
    def __init__(self):
        self.result = None
        self.mini_date = datetime.date.today()

    def screen_by_mini_date(self, urls: list, queue: SimpleQueue):
        for url in urls:
            req = self.result.urls_detail[url]
            req.encoding = req.apparent_encoding
            if req.encoding.lower() == 'gb2312' or req.encoding.lower() == 'gbk':
                req.encoding = 'gb18030'
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
        downloader = Downloader(Config("hardworking_av_studio.ini"))
        process_number = int(downloader.config.ini['multi']['process_number'])
        urls = ['https://www.dmmsee.zone/studio/0']
        urls.extend(['https://www.dmmsee.zone/studio/{}{}'.format(i, word) for i in range(1, 40) for word in
                     ' ' + string.ascii_lowercase])
        urls.extend(['https://www.dmmsee.zone/studio/{}'.format(i) for i in range(40, 400)])
        print(" config ".center(60, '*'))
        downloader.config.list_config()
        print(" download urls ".center(60, '*'))
        self.result = downloader.get_result(urls)
        self.result.show_time_cost()
        self.result.show_urls_status()
        print(" retry failed urls ".center(60, '*'))
        self.result.retry_failed_urls()
        self.result.show_urls_status()

        if os.path.exists("hardworking_av_studio.txt"):
            os.remove("hardworking_av_studio.txt")

        print(" analyzing result ".center(60, '*'))
        tmp_time = time.time()
        process_number = int(process_number // 1.5) if process_number > 2 else process_number
        queue = SimpleQueue()
        for i in range(process_number):
            Process(target=self.screen_by_mini_date, args=(self.result.finished_urls[i::process_number]
                                                           , queue)).start()
        for i in tqdm(range(len(self.result.finished_urls)), total=len(self.result.finished_urls),
                      desc="analyzing result", unit="result", postfix={"process": process_number}):
            queue.get()
        print("\nanalysis completed... time cost {:.2f}s".format(time.time() - tmp_time))
        print(" result ".center(60, '*'))
        print("The result has been written to the current folder:",
              os.path.join(os.getcwd(), "hardworking_av_studio.txt"))
        return True


if __name__ == '__main__':
    freeze_support()
    t1 = time.time()
    HardworkingAvStudio().start()
    print("total time cost {:.2f}s".format(time.time() - t1))
    input("press enter to exit...")
