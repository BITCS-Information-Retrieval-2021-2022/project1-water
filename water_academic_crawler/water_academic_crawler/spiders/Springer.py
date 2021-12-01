# -*- coding: utf-8 -*-
from scrapy import Request
from scrapy.spiders import Spider
from scrapy.loader import ItemLoader
from water_academic_crawler.settings import SPRINGER_CHECKPOINT_PATH
from water_academic_crawler.items import AcademicItem
from water_academic_crawler.util import load_checkpoint, set_checkpoint


class SpringerSpirder(Spider):
    name = 'Springer'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        checkpoint = load_checkpoint(SPRINGER_CHECKPOINT_PATH)
        print(checkpoint)
        self.page = checkpoint['page']
        self.year = checkpoint['year']

    def start_requests(self):
        url = 'https://link.springer.com/search/page/' + str(self.page) + '?facet-end-year=' + str(self.year) \
              + '&facet-content-type=%22ConferencePaper%22&facet-discipline=%22Computer+Science%22&date-facet-mode' \
                '=between&facet-start-year=' + str(self.year)
        yield Request(url, callback=self.parse_result_page, dont_filter=True, meta={'total_page': -1})

    def parse_result_page(self, response):
        if response.request.meta['total_page'] == -1:
            total_page = int(
                response.xpath('//span[contains(@class,"number-of-pages")]/text()').extract()[0].replace(',', ''))
        else:
            total_page = response.request.meta['total_page']

        result_selectors = response.xpath('//*[@id="results-list"]/li')
        for s in result_selectors:
            paper_url = 'https://link.springer.com' + s.xpath('./h2/a/@href').extract()[0]
            venue = s.xpath('./p[contains(@class,"meta")]/span[2]/a/text()').extract()[0]
            yield Request(url=paper_url, callback=self.parse_chapter, dont_filter=True,
                          meta={'url': paper_url, 'venue': venue})
        self.page = self.page + 1
        new_total = total_page
        if self.page > 999 or self.page > total_page:
            self.year = self.year + 1
            if self.year > 2022:
                print('=== Finish ===')
                self.crawler.engine.close_spider(self, 'Finished.')
                return
            self.page = 1
            new_total = -1
        self.set_checkpoint()
        list_url = 'https://link.springer.com/search/page/' + str(self.page) + '?facet-end-year=' + str(self.year) \
                   + '&facet-content-type=%22ConferencePaper%22&facet-discipline=%22Computer+Science%22&date-facet-mode' \
                     '=between&facet-start-year=' + str(self.year)
        yield Request(url=list_url, callback=self.parse_result_page, dont_filter=True, meta={'total_page': new_total})

    def set_checkpoint(self):
        checkpoint = {
            'page': self.page,
            'year': self.year
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
        paper.add_value('month', 'N/A')
        paper.add_xpath('type', '//*[@id="main-content"]/div/div/article/div/div[1]/div[4]/div[1]/span/span/text()')
        paper.add_value('venue', response.request.meta['venue'])
        paper.add_value('source', 'Springer')
        # 没有提供video_url, thumbnail_url，故video_path也为空
        paper.add_value('video_url', 'N/A')
        paper.add_value('thumbnail_url', 'N/A')
        paper.add_value('video_path', 'N/A')
        paper.add_xpath('pdf_url', '//meta[contains(@name,"citation_pdf_url")]/@content')
        # pdf_path交由后续pipeline处理
        paper.add_value('pdf_path', 'N/A')
        # 没有提供inCitations数据
        paper.add_value('inCitations', 'N/A')
        outCitations_selector = response.xpath('//ol[contains(@class,"BibliographyWrapper")]/li').extract()
        paper.add_xpath('outCitations', str(len(outCitations_selector)))
        yield paper.load_item()
