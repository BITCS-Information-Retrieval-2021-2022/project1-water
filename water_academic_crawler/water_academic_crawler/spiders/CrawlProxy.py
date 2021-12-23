from scrapy.spiders import Spider
import json
import scrapy
from scrapy.crawler import CrawlerProcess

HEADERS = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) \
    Chrome/80.0.3987.116 Safari/537.36'}


class Proxyitem(scrapy.Item):
    proxy = scrapy.Field()


class CrawlProxy(Spider):
    name = 'CrawlProxy'

    def start_requests(self):
        url = 'http://www.xiladaili.com/gaoni/'
        req = scrapy.Request(url=url, headers=HEADERS, callback=self.parse)
        yield req

    def parse(self, response):
        for i in range(1, 50):
            selector = response.xpath(f'/html/body/div/div[3]/div[2]/table/tbody/tr[{i}]/td[1]')
            item = Proxyitem()
            item['proxy'] = selector[0].root.text
            yield item


if __name__ == '__main__':
    # 便于调试，输出item到指定文件和指定打印日志等级
    process = CrawlerProcess(settings={
        "FEEDS": {
            "../proxy/proxy.json": {"format": "json"},
        },
        "LOG_LEVEL": "INFO"
    })

    process.crawl(CrawlProxy)
    process.start()  # the script will block here until the crawling is finished
