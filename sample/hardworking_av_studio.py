import string
from crawler.core import Downloader, Config, Result
from concurrent.futures import ProcessPoolExecutor, wait, ALL_COMPLETED
import time
from bs4 import BeautifulSoup
import datetime
import os


def screen_by_mini_date(result: Result, urls: list, mini_date):
    for url in urls:
        req = result.urls_detail[url]
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
            if content_date.__gt__(mini_date):
                with open("hardworking_av_studio.txt", 'a+', encoding='utf-8') as file:
                    file.write(str(url) + ' : ' + str(content_date) + '\n')
    return True


if __name__ == '__main__':
    downloader = Downloader(Config("hardworking_av_studio.ini"))
    process_number = int(downloader.config.ini['multi']['process_number'])

    urls = ['https://www.dmmsee.zone/studio/0']
    urls.extend(['https://www.dmmsee.zone/studio/{}{}'.format(i, word) for i in range(1, 40) for word in
                 ' ' + string.ascii_lowercase])
    urls.extend(['https://www.dmmsee.zone/studio/{}'.format(i) for i in range(40, 400)])
    print('******************config********************')
    downloader.config.list_config()
    print('********************************************')
    result = downloader.get_result(urls)
    result.show_time_cost()
    result.retry_failed_urls()

    mini_date = datetime.date.today()
    t1 = time.time()
    process_pool_executor = ProcessPoolExecutor(process_number)
    process_futures = []
    if os.path.exists("hardworking_av_studio.txt"):
        os.remove("hardworking_av_studio.txt")
    print("start analysis...")
    for i in range(process_number):
        future = process_pool_executor.submit(screen_by_mini_date, result
                                              , result.finished_urls[i::process_number], mini_date)
        process_futures.append(future)
    wait(process_futures, return_when=ALL_COMPLETED)
    print("analysis cost {:.2f} seconds".format(time.time() - t1))
