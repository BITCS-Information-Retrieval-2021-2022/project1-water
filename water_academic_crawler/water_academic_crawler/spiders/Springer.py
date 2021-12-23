# -*- coding: utf-8 -*-
import math

from scrapy import Request
from scrapy.spiders import Spider
from scrapy.loader import ItemLoader
from water_academic_crawler.settings import SPRINGER_CHECKPOINT_PATH, SPRINGER_SUBDISCIPLINE_PATH
from water_academic_crawler.items import AcademicItem
from water_academic_crawler.util import load_checkpoint, set_checkpoint, load_subdiscipline_list


class SpringerSpirder(Spider):
    name = 'Springer'
    subdiscipline_list = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.subdiscipline_list = load_subdiscipline_list(SPRINGER_SUBDISCIPLINE_PATH)
        checkpoint = load_checkpoint(SPRINGER_CHECKPOINT_PATH)
        print(checkpoint)
        self.page = checkpoint['page']
        self.year = checkpoint['year']
        self.subdiscipline = checkpoint['subdiscipline']

    def start_requests(self):
        url = 'https://link.springer.com/search/page/' + str(self.page) + '?facet-end-year=' + str(self.year) \
              + '&facet-content-type=%22ConferencePaper%22&facet-sub-discipline=%22' + self.subdiscipline_list[
                  self.subdiscipline] + '%22&date-facet-mode' \
                                        '=between&facet-start-year=' + str(self.year)
        yield Request(url, callback=self.parse_result_page, dont_filter=True, meta={'total_page': -1})

    def parse_result_page(self, response):
        if response.request.meta['total_page'] == -1:
            total = response.xpath('//*[@id="number-of-search-results-and-search-terms"]/strong/text()').extract()[0]
            total_page = math.ceil(int(total.replace(',', '')) / 20)
        else:
            total_page = response.request.meta['total_page']

        result_selectors = response.xpath('//*[@id="results-list"]/li')
        for s in result_selectors:
            paper_url = 'https://link.springer.com' + s.xpath('./h2/a/@href').extract()[0]
            venue = s.xpath('./p[contains(@class,"meta")]/span[contains(@class,"enumeration")]/a/text()').extract()[0]
            yield Request(url=paper_url, callback=self.parse_chapter, dont_filter=True,
                          meta={'url': paper_url, 'venue': venue})
        self.page = self.page + 1
        new_total = total_page
        if self.page > 999 or self.page > total_page:
            self.year = self.year + 1
            if self.year > 2022:
                self.subdiscipline = self.subdiscipline + 1
                self.year = 1930
                if self.subdiscipline >= len(self.subdiscipline_list):
                    print('=== Finish ===')
                    self.crawler.engine.close_spider(self, 'Finished.')
                    return
            self.page = 1
            new_total = -1
        self.set_checkpoint()
        list_url = 'https://link.springer.com/search/page/' + str(self.page) + '?facet-end-year=' + str(self.year) \
                   + '&facet-content-type=%22ConferencePaper%22&facet-sub-discipline=%22' + self.subdiscipline_list[
                       self.subdiscipline] + '%22&date-facet-mode' \
                                             '=between&facet-start-year=' + str(self.year)
        yield Request(url=list_url, callback=self.parse_result_page, dont_filter=True, meta={'total_page': new_total})

    def set_checkpoint(self):
        checkpoint = {
            'page': self.page,
            'year': self.year,
            'subdiscipline': self.subdiscipline
        }
        print(checkpoint)
        set_checkpoint(SPRINGER_CHECKPOINT_PATH, checkpoint, 'w+')

    def parse_chapter(self, response):
        paper = ItemLoader(item=AcademicItem(), selector=response)

        paper.add_xpath('title', '//*[@id="main-content"]/div/div/article/div/div[1]/div[2]/h1/text()')
        paper.add_xpath('abstract', '//*[@id="Abs1"]/p/text()')
        authors_selector = response.xpath('//span[contains(@class,"authors__name")]/text()')
        authors = ''
        for s in authors_selector:
            authors = authors + s.extract() + '|'
        paper.add_value('authors', authors)
        paper.add_xpath('doi', '//*[@id="doi-url"]/text()')
        paper.add_value('url', response.request.meta['url'])
        paper.add_xpath('year', '//*[@id="main-content"]/div/div/article/div/div[1]/div[4]/div[1]/div/span['
                                '2]/time/text()')
        paper.add_value('month', '__N/A__')
        paper.add_xpath('type', '//*[@id="main-content"]/div/div/article/div/div[1]/div[4]/div[1]/span/span/text()')
        paper.add_value('venue', response.request.meta['venue'])
        paper.add_value('source', 'Springer')
        # 没有提供video_url, thumbnail_url，故video_path也为空
        paper.add_value('video_url', '__N/A__')
        paper.add_value('thumbnail_url', '__N/A__')
        paper.add_value('video_path', '__N/A__')
        paper.add_xpath('pdf_url', '//meta[contains(@name,"citation_pdf_url")]/@content')
        # pdf_path交由后续pipeline处理
        paper.add_value('pdf_path', '__N/A__')
        # 没有提供inCitations数据
        paper.add_value('inCitations', '__N/A__')
        outCitations_selector = response.xpath('//ol[contains(@class,"BibliographyWrapper")]/li').extract()
        paper.add_xpath('outCitations', str(len(outCitations_selector)))
        yield paper.load_item()
