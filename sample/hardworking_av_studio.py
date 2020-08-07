from crawler.core import Downloader, Config
from multiprocessing import Process, Queue, freeze_support
from bs4 import BeautifulSoup
import datetime
import os
from tqdm import tqdm
import string


class HardworkingAvStudio:
    def __init__(self):
        self.result = None
        self.mini_date = datetime.date.today()

    def screen_by_mini_date(self, urls: list, queue: Queue):
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
        print('******************config********************')
        downloader.config.list_config()
        print('********************************************')
        self.result = downloader.get_result(urls)
        self.result.show_time_cost()
        self.result.retry_failed_urls()

        if os.path.exists("hardworking_av_studio.txt"):
            os.remove("hardworking_av_studio.txt")
        queue = Queue()
        print("start analyzing...")
        # 调试
        process_number = process_number // 1.5 if process_number > 2 else process_number
        for i in range(process_number):
            Process(target=self.screen_by_mini_date, args=(self.result.finished_urls[i::process_number]
                                                           , queue)).start()
        p_bar = tqdm(total=len(self.result.finished_urls), desc="analyzing result", unit="result")
        for i in range(len(self.result.finished_urls)):
            queue.get()
            p_bar.update(1)
        queue.close()
        print("\nanalysis completed...")
        print("********************************************")
        print("The result has been written to the current folder:",
              os.path.join(os.getcwd(), "hardworking_av_studio.txt"))
        input("press enter to exit...")


if __name__ == '__main__':
    freeze_support()
    HardworkingAvStudio().start()
