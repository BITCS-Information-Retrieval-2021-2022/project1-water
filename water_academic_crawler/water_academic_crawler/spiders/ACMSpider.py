# -*- coding: utf-8 -*-
from scrapy import Request
from scrapy.spiders import Spider
from water_academic_crawler.items import AcademicItem
from scrapy.loader import ItemLoader


class ACMSpider(Spider):
    name = 'ACM'

    def start_requests(self):
        url = 'https://dl.acm.org/doi/10.1145/3404835.3462936'
        yield Request(url, callback=self.ACM_parse)

    def ACM_parse(self, response):
        paper = ItemLoader(item=AcademicItem(), selector=response)

        paper.add_xpath('title', '//*[@id="pb-page-content"]/div/main/div[2]/article/div[1]/div[2]/div/div/div['
                                 '2]/h1/text()')
        paper.add_xpath('abstract', '//*[@id="pb-page-content"]/div/main/div[2]/article/div[2]/div[2]/div[2]/div['
                                    '1]/div/div[2]/p/text()')
        authors_selector = response.xpath('//span[@class="loa__author-name"]/span/text()')
        authors = ''
        for s in authors_selector:
            authors = authors + s.extract() + '|'
        paper.add_value('authors', authors)
        paper.add_xpath('doi', '//*[@id="pb-page-content"]/div/main/div[2]/article/div[1]/div[2]/div/div/div['
                               '4]/div/span[3]/a/text()')
        # todo url
        paper.add_xpath('year', '//*[@id="pb-page-content"]/div/main/div[2]/article/div[1]/div[2]/div/div/div['
                                '4]/div/span[1]/span/text()')
        paper.add_xpath('month', '//*[@id="pb-page-content"]/div/main/div[2]/article/div[1]/div[2]/div/div/div['
                                 '4]/div/span[1]/span/text()')
        # todo type
        paper.add_xpath('venue', '//*[@id="pb-page-content"]/div/main/div[2]/article/div[1]/div[2]/div/div/div['
                                 '4]/div/a/span/text()')
        paper.add_value('source', 'ACM')
        paper.add_xpath('video_url', '//*[@id="pb-page-content"]/div/main/div[2]/article/div[2]/div[2]/div[2]/div['
                                     '3]/div[2]/div/div/div/div[2]/div/div/div[2]/a[2]/@href')
        # todo video_path
        paper.add_xpath('thumbnail_url', '/html/body/div[1]/div/main/div[2]/article/div[2]/div[2]/div[2]/div[3]/div['
                                         '2]/div/div/div/div[1]/div/stream/@poster')
        paper.add_xpath('pdf_url', '//*[@id="pb-page-content"]/div/main/div[2]/article/div[1]/div[2]/div/div/div['
                                   '6]/div/div[2]/ul[2]/li[2]/a/@href')
        # todo pdf_path
        paper.add_xpath('inCitations', '//*[@id="pb-page-content"]/div/main/div[2]/article/div[1]/div[2]/div/div/div['
                                       '6]/div/div[1]/div/ul/li[1]/span/span[1]/text()')
        paper.add_xpath('outCitations', '//*[@id="pb-page-content"]/div/main/div[2]/article/div[2]/div[3]/div/ul/li['
                                        '4]/a/span/text()')

        yield paper.load_item()
