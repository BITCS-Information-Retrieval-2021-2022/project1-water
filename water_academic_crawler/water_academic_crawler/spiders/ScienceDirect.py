from scrapy.spiders import Spider
import json
import scrapy
from scrapy.crawler import CrawlerProcess
from water_academic_crawler.items import AcademicItem
import re
import os
from water_academic_crawler.util import save_ckpt, \
    load_ckpt, get_printable_text
from water_academic_crawler.settings import \
    CKPT_PATH_SCIENCEDIRECT, CKPT_FLAG_SCIENCEDIRECT
import time as T

HEADERS = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) '
                         'AppleWebKit/537.36 (KHTML, like Gecko) \
    Chrome/80.0.3987.116 Safari/537.36'}
HEADERS_SEC = {'user-agent': 'Chrome/96.0.4664.45'}
# '2827ed44c4e21ec313f7b086ae412420'
Api_Key = '7f59af901d2d86f78a1fd60c1bf9426a'


class ScienceDirect(Spider):
    name = 'ScienceDirect'

    def __init__(self):
        self.word_list = ["Transformer", "Bert", "LSTM", "attention"]
        self.word_list_tmp = ["Transformer", "Bert", "LSTM", "attention"]
        self.new_key_words = []
        self.paper_list = []

    def start_requests(self):

        keyword = self.word_list_tmp[0]

        self.word_list_tmp.pop(0)
        # 构造url, get 方法
        url = f'https://api.elsevier.com/content/search/' \
              f'sciencedirect?query={keyword}' \
              f'&count=100&apiKey={Api_Key}&httpAccept=application%2Fjson'
        # 创建 scrapy.Request 实例
        if os.path.exists(CKPT_PATH_SCIENCEDIRECT) and CKPT_FLAG_SCIENCEDIRECT:
            url, self.word_list, self.word_list_tmp = \
                load_ckpt(CKPT_PATH_SCIENCEDIRECT)
        req = scrapy.Request(url=url,
                             headers=HEADERS,
                             callback=self.parse)
        yield req

    def parse(self, response):
        paper_list_tmp = []

        item = AcademicItem()
        result = json.loads(response.text)
        result = result["search-results"]
        links = result["link"]
        entry = result["entry"]
        print('--------------------------')
        now_link = links[0]['@href']
        next_link = [x for x in links if x['@ref'] == 'next']
        if len(next_link) > 0:
            next_link = next_link[0]['@href']
        else:
            next_link = now_link
        page = re.findall(r"start=(.+?)&", string=now_link)
        word = re.findall(r"query=(.+?)&", string=now_link)
        print(f'now crawling word {word}, {page} of 6000')

        for paper in entry:
            item['title'] = get_printable_text(paper[r'dc:title'])
            if paper[r'dc:title'] in self.paper_list:
                continue
            self.paper_list.append(paper[r'dc:title'])
            paper_list_tmp.append(paper[r'dc:title'])
            # item = self.func(item)
            try:
                authors = paper['authors']['author']
                if isinstance(authors, str):
                    item['authors'] = [authors]
                else:
                    item['authors'] = [x["$"] for x in authors]
            except TypeError:
                item['authors'] = []

            try:
                item['doi'] = r"https://doi.org/" + paper['prism:doi']
            except KeyError:
                pass

            item['url'] = (paper['link'][1]['@href']) \
                .rstrip(r'?dgcid=api_sd_search-api-endpoint')
            item['pdf_url'] = item['url'] + '/pdfft'
            item['pdf_path'] = 'storage/pdf/' + item['title'] + '.pdf'
            time = paper['load-date'].split('-')
            item['year'] = time[0]
            item['month'] = time[1]
            item['venue'] = paper['prism:publicationName']
            item['source'] = 'ScienceDirect'
            # yield item
            request_second = scrapy.Request(url=item['url'],
                                            headers=HEADERS,
                                            callback=self.second_parse,
                                            priority=20,
                                            meta={'item': item.deepcopy()})
            yield request_second

        for title in paper_list_tmp:
            words = title.split(' ')
            for word in words:
                if (len(word) > 5 or (word.isupper() and len(word) > 2)) \
                        and len(self.word_list_tmp) < 1000:
                    if word in self.word_list:
                        continue
                    self.word_list.append(word)
                    self.word_list_tmp.append(word)

        # print(f'words to crawl = {len(self.word_list_tmp)}:')

        if not now_link == links[3]['@href']:
            # T.sleep(0.5)
            req = scrapy.Request(url=next_link,
                                 headers=HEADERS, callback=self.parse)
            save_ckpt(next_link, self.word_list,
                      self.word_list_tmp, CKPT_PATH_SCIENCEDIRECT)
            yield req
        else:
            url = f'https://api.elsevier.com/content/search/sciencedirect?' \
                  f'query={self.word_list_tmp.pop(0)}' \
                  f'&count=100&apiKey={Api_Key}&httpAccept=application%2Fjson'
            save_ckpt(url, self.word_list,
                      self.word_list_tmp, CKPT_PATH_SCIENCEDIRECT)
            req = scrapy.Request(url=url, headers=HEADERS, callback=self.parse)
            yield req

    def second_parse(self, response):
        item = response.request.meta['item']
        response.xpath('/html')
        body = str(response.body)
        md5 = re.findall(r"\"md5\":\"(.+?)\"", string=body)
        pid = re.findall(r"\"pid\":\"(.+?)\"", string=body)
        url = ''
        if md5 != [] and pid != []:
            md5 = md5[0]
            pid = pid[0]
            url = response.request.url + '/pdfft?md5=' + md5 + '&pid=' + pid
            item['pdf_url'] = url

        abstract = re.findall(r"Abstract</h2>(.+?)</div>", string=body)
        if abstract != []:
            abstract = re.sub(r"<.*?>", "", string=abstract[0])
            item['abstract'] = get_printable_text(abstract)
            item['pdf_path'] = 'storage/pdf/' + item['title'] + '.pdf'

        return item


if __name__ == '__main__':
    # 便于调试，输出item到指定文件和指定打印日志等级
    process = CrawlerProcess(settings={
        "FEEDS": {
            "items.json": {"format": "json"},
        },
        "LOG_LEVEL": "INFO"
    })

    process.crawl(ScienceDirect)
    process.start()
