from crawler.core import Downloader, Config
from bs4 import BeautifulSoup
import time
from urllib import parse
import re
from multiprocessing import SimpleQueue, Process, freeze_support, cpu_count
from tqdm import tqdm
import os
import shutil

SERVER = 'https://so.biqusoso.com/s.php?ie=utf-8&siteid=biqukan.com&q='

NOVEL_DOWNLOADER_CONFIG_DICT = {'multi': {'process_number': cpu_count(),
                                          'thread_number': 5,
                                          'delay': 1.0},
                                'proxy': {'proxy_url': '',
                                          'timeout': 10.0,
                                          'retry': 3}
                                }


class NovelDownloader:
    def __init__(self):
        self.novel_name = None
        self.downloader = Downloader(Config("novel_downloader.ini", NOVEL_DOWNLOADER_CONFIG_DICT))
        self.downloader.enable_chinese_transcoding()

    def find_novel(self):
        while True:
            self.novel_name = input('请输入小说名称: ')
            t1 = time.time()
            url = SERVER + self.novel_name
            req = self.downloader.get_req(url)
            soup = BeautifulSoup(req.text, features='lxml')
            soup.prettify()
            s2 = soup.find_all(class_='s2')
            if len(s2) >= 2:
                text = s2[1].text
                href = next(s2[1].children).get('href')
                for span in s2:
                    if span.text == self.novel_name:
                        text = span.text
                        href = next(span.children).get('href')
                        break
                self.novel_name = text
                print("搜索到小说: 《{}》, 耗时: {:.2f}s".format(novel_downloader.novel_name, time.time() - t1))
                return href
            print("查无此小说, 请重试")

    def get_chapter_url_list(self, url: str) -> list:
        def novel_start(chapter_name):
            start_pattern = '第' + '[0零]*' + '[零01一]' + '章'
            return re.match(start_pattern, chapter_name)

        req = self.downloader.get_req(url)
        soup = BeautifulSoup(req.text, features='lxml')
        soup.prettify()
        div = soup.find_all('div', class_='listmain')
        a_soup = BeautifulSoup(str(div[0]), features='lxml')
        a = a_soup.find_all('a')

        chapter_url_list = []
        start_flag = False
        for each in a:
            if start_flag == 0 and (novel_start(each.get_text()) is not None):
                start_flag = 1
                chapter_url_list.append(parse.urljoin(url, each.get('href')))
            elif start_flag == 1:
                chapter_url_list.append(parse.urljoin(url, each.get('href')))
        return chapter_url_list

    @staticmethod
    def fill_novel_dict(urls, novel_dict, queue):
        advertising_pattern = r'\r|&1t;p&gt;|&1t;/p&gt;|&1t;i&gt;|&1t;/i&gt;' \
                              r'|手机阅读地址：http://m.biqukan.com，数据和书签与电脑站同步，无广告清新阅读！' \
                              r'|水印广告测试' \
                              r'|手机阅读：m.biqukan.com' \
                              r'|百度搜索“笔趣看小说网”' \
                              r'|;\[笔趣看  www.biqukan.com\]'
        end_line_pattern = r'<br {0,1}/>'
        for url in urls:
            req = novel_dict[url]
            if isinstance(req, Exception):
                novel_dict[url] = repr(req)

            text = re.sub(advertising_pattern, '', req.text)
            text = re.sub(end_line_pattern, '\r\n', text)

            soup = BeautifulSoup(text, features='lxml')
            soup.prettify()

            texts = soup.find_all('div', class_='showtxt')
            h1 = soup.find('h1')

            span = re.search("https://www.biqukan.com", texts[0].text)
            if span is not None:
                bi_qu_kan_advertising = span.span()[0] - 1
            else:
                bi_qu_kan_advertising = -1
            novel_dict[url] = h1.text + '\r\n' + texts[0].text[:bi_qu_kan_advertising]
            queue.put(url)
        return True

    def get_novel_dict(self, chapter_url_list: list) -> dict:
        result = self.downloader.get_result(chapter_url_list)
        result.show_time_cost()
        result.show_urls_status()
        print(" 重试失败章节 ".center(shutil.get_terminal_size().columns - 7, '*'))
        result.retry_failed_urls()
        result.show_urls_status()

        print(" 分离章节内容 ".center(shutil.get_terminal_size().columns - 7, '*'))
        process_number = self.downloader.config.get_config("multi", "process_number")
        process_number = int(process_number // 1.5) if process_number > 2 else process_number
        queue = SimpleQueue()
        for i in range(process_number):
            Process(target=self.fill_novel_dict, args=(chapter_url_list[i::process_number]
                                                       , result.get_urls_detail_dict(), queue)).start()
        for i in tqdm(range(len(chapter_url_list)), total=len(chapter_url_list),
                      desc="分离章节内容", unit="章节", postfix={"process": process_number}):
            queue.get()

        return result.get_urls_detail_dict()

    def start(self):
        print(" 配置文件 ".center(shutil.get_terminal_size().columns - 5, '*'))
        self.downloader.config.list_config()
        print(" 搜索小说 ".center(shutil.get_terminal_size().columns - 5, '*'))
        novel_chapter_url = self.find_novel()
        t1 = time.time()
        chapter_url_list = self.get_chapter_url_list(novel_chapter_url)
        print("分析章节列表完成, 耗时: {:.2f}s".format(time.time() - t1))
        print(" 下载小说 ".center(shutil.get_terminal_size().columns - 5, '*'))
        novel_dict = self.get_novel_dict(chapter_url_list)
        print(" 小说写入文件 ".center(shutil.get_terminal_size().columns - 7, '*'))
        with open(self.novel_name + '.txt', 'w+', encoding='utf-8') as file:
            for chapter_url in chapter_url_list:
                file.write(novel_dict[chapter_url])
        print('小说写入完成, 总耗时: {:.2f}s'.format(time.time() - t1))
        print('小说位置: ', os.path.join(os.getcwd(), self.novel_name + '.txt'))


if __name__ == '__main__':
    freeze_support()
    novel_downloader = NovelDownloader()
    novel_downloader.start()
    input('press enter to exit...')
