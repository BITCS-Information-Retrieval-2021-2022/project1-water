from scrapy.spiders import Spider
import json
import scrapy
from scrapy.crawler import CrawlerProcess
from water_academic_crawler.items import AcademicItem
from water_academic_crawler.items import PDFItem
import re
import time as T

HEADERS = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) \
    Chrome/80.0.3987.116 Safari/537.36'}
HEADERS_SEC = {'user-agent': 'Chrome/96.0.4664.45'}
HEADERS_AUTH = {'Content-Type': 'application/json', 'Accept': 'application/json', 'x-els-apikey': '7f59af901d2d86f78a1fd60c1bf9426a',}
HEADER_POST ={}
HEADER_POST.update(HEADERS)
HEADER_POST.update(HEADERS_AUTH)
Api_Key = '7f59af901d2d86f78a1fd60c1bf9426a' # '2827ed44c4e21ec313f7b086ae412420'

class ScienceDirectDetails(Spider):
    name = 'ScienceDirectDetails'

    def start_requests(self):
        url = rf'https://www.sciencedirect.com/science/article/pii/S0925231221015253'
        req = scrapy.Request(url=url, headers=HEADERS_SEC, callback=self.parse)
        yield req

    def parse(self, response):
        response.xpath('/html')
        body = str(response.body)
        md5 = re.findall(r"\"md5\":\"(.+?)\"",string=body)
        pid = re.findall(r"\"pid\":\"(.+?)\"",string=body)
        if md5 != [] and pid != []:
            md5 = md5[0]
            pid = pid[0]
            url = response.request.url + '/pdfft?md5=' + md5 +'&pid=' + pid
        abstract = re.findall(r"<p id=\"sp005\">(.+?)</p>",string=body)
        if abstract != []:
            abstract = re.sub(r"<.*?>","",string=abstract[0])
        print(url)
        # print(abstract)
        item = PDFItem()
        item['file_names'] = pid.strip('.pdf')
        item['file_urls'] = url
        yield item



if __name__ == '__main__':
    # 便于调试，输出item到指定文件和指定打印日志等级
    process = CrawlerProcess(settings={
        "FEEDS": {
            "items.json": {"format": "json"},
        },
        "LOG_LEVEL" : "INFO"
    })

    process.crawl(ScienceDirectDetails)
    process.start()  # the script will block here until the crawling is finished