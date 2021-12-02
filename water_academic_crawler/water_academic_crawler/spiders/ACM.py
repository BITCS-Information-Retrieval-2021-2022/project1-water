# -*- coding: utf-8 -*-
from scrapy import Request
from scrapy.spiders import Spider
from scrapy.loader import ItemLoader
from water_academic_crawler.settings import ACM_CHECKPOINT_PATH, ACM_MAX_CONCEPT_ID
from water_academic_crawler.items import AcademicItem
from water_academic_crawler.util import load_checkpoint, set_checkpoint

HEADERS = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/96.0.4664.45 Safari/537.36'}


class ACMSpider(Spider):
    name = 'ACM'
    handle_httpstatus_list = [403]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        checkpoint = load_checkpoint(ACM_CHECKPOINT_PATH)
        self.current_concept = checkpoint['current_concept']
        self.page = checkpoint['page']

    def start_requests(self):
        url = 'https://dl.acm.org/action/doSearch?ConceptID=' + str(
            self.current_concept) + '&expand=all&pageSize=20&startPage=' + str(
            self.page) + '&ContentItemType=research-article'
        print('Crawling ConceptID: %d, page: %d' % (self.current_concept, self.page))
        yield Request(url, headers=HEADERS, callback=self.parse_result_page, dont_filter=True)
        # url = 'https://dl.acm.org/doi/10.1145/3485522'
        # yield Request(url, headers=HEADERS, callback=self.parse_paper, dont_filter=True, meta={'url': url})

    def parse_result_page(self, response):
        if response.status == 403:
            print('Banned by ACM Digit Library. Current ConceptID: %d, page: %s. Saving to checkpoint.' % (
                self.current_concept, self.page))
            self.set_checkpoint()
            self.crawler.engine.close_spider(self, 'Banned by ACM Digit Library.')
            return

        total_results = response.xpath('//*[@id="pb-page-content"]/div/main/div[1]/div/div[2]/div/div[1]/div[1]/span['
                                       '2]/span[1]/text()').extract()[0]
        total_pages = int(int(total_results.replace(',', '')) / 20)

        result_selectors = response.xpath('//li[contains(@class,"search__item issue-item-container")]')
        for s in result_selectors:
            paper_url = 'https://dl.acm.org' + s.xpath('div[2]/div[2]/div/h5/span/a/@href').extract()[0]
            yield Request(url=paper_url, callback=self.parse_paper, meta={'url': paper_url}, dont_filter=True)

        self.page = self.page + 1
        if self.page > 100 or self.page > total_pages:  # ACM只返回前2000条数据，多了没有意义
            self.current_concept = self.current_concept + 1
            if self.current_concept > ACM_MAX_CONCEPT_ID:
                print('=== Finish ===')
                self.crawler.engine.close_spider(self, 'Finished.')
                return
            self.page = 0
        self.set_checkpoint()
        url = 'https://dl.acm.org/action/doSearch?ConceptID=' + str(
            self.current_concept) + '&expand=all&pageSize=20&startPage=' + str(
            self.page) + '&ContentItemType=research-article'
        print('Crawling ConceptID: %d, page: %d' % (self.current_concept, self.page))
        yield Request(url, headers=HEADERS, callback=self.parse_result_page, dont_filter=True)

    def set_checkpoint(self):
        checkpoint = {
            'current_concept': self.current_concept,
            'page': self.page,
        }
        set_checkpoint(ACM_CHECKPOINT_PATH, checkpoint, 'w+')

    def parse_paper(self, response):
        if response.status == 403:
            print('Banned by ACM Digit Library. Current ConceptID: %d, page: %s. Saving to checkpoint.' % (
                self.current_concept, self.page))
            self.set_checkpoint()
            self.crawler.engine.close_spider(self, 'Banned by ACM Digit Library.')
            return

        paper = ItemLoader(item=AcademicItem(), selector=response)
        paper.add_xpath('title', '//*[@id="pb-page-content"]/div/main/div[2]/article/div[1]/div[2]/div/div/div['
                                 '2]/h1/text()')
        paper.add_xpath('abstract', '//div[contains(@class,"abstractSection abstractInFull")]//p/text()')
        # 拼接为|分割的字符串，在pipeline中处理
        authors_selector = response.xpath('//span[@class="loa__author-name"]/span/text()')
        authors = ''
        for s in authors_selector:
            authors = authors + s.extract() + '|'
        paper.add_value('authors', authors)
        paper.add_value('doi', response.request.meta['url'].replace('https://dl.acm.org', 'https:/'))
        paper.add_value('url', response.request.meta['url'])
        paper.add_xpath('year', '//span[contains(@class,"CitationCoverDate")]/text()')
        paper.add_value('month', '__N/A__')
        # 交由后续pipeline进一步判断文章类型
        navigator_selectors = response.xpath('//*[@id="pb-page-content"]/div/header/div[4]/div/div/nav/a/text()')
        navigator = ''
        for s in navigator_selectors:
            navigator = navigator + s.extract() + '|'
        paper.add_value('type', navigator)
        paper.add_xpath('venue', '//*[@id="pb-page-content"]/div/main/div[2]/article/div[1]/div[2]/div/div/div['
                                 '4]/div/a/span/text()')
        paper.add_value('source', 'ACM')
        paper.add_xpath('video_url', '//*[@id="pb-page-content"]/div/main/div[2]/article/div[2]/div[2]/div[2]/div['
                                     '3]/div[2]/div/div/div/div[2]/div/div/div[2]/a[2]/@href')
        # video_path交由后续pipeline处理
        paper.add_value('video_path', '__N/A__')
        paper.add_xpath('thumbnail_url', '/html/body/div[1]/div/main/div[2]/article/div[2]/div[2]/div[2]/div[3]/div['
                                         '2]/div/div/div/div[1]/div/stream/@poster')
        paper.add_xpath('pdf_url', '//*[@id="pb-page-content"]/div/main/div[2]/article/div[1]/div[2]/div/div/div['
                                   '6]/div/div[2]/ul[2]/li[2]/a/@href')
        # pdf_path交由后续pipeline处理
        paper.add_value('pdf_path', '__N/A__')
        paper.add_xpath('inCitations', '//span[contains(@class,"citation")]/span[1]/text()')
        outCitations_selector = response.xpath('//ol[contains(@class,"rlist references__list")]/li').extract()
        paper.add_xpath('outCitations', str(int(len(outCitations_selector))))

        yield paper.load_item()
