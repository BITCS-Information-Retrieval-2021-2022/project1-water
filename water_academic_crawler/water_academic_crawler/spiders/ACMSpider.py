# -*- coding: utf-8 -*-
from scrapy import Request
from scrapy.spiders import Spider
from scrapy.loader import ItemLoader
from water_academic_crawler.settings import ACM_CHECKPOINT_PATH
from water_academic_crawler.items import AcademicItem
from water_academic_crawler.util import load_checkpoint, set_checkpoint

HEADERS = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/96.0.4664.45 Safari/537.36'}


class ACMSpider(Spider):
    name = 'ACM'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        checkpoint = load_checkpoint(ACM_CHECKPOINT_PATH)
        self.candidate_list = checkpoint['candidate_list']
        self.current_word = checkpoint['current_word']
        if self.current_word == '':
            self.current_word = self.candidate_list.pop()
        self.page = checkpoint['page']
        self.used_list = checkpoint['used_list']

    def start_requests(self):
        url = 'https://dl.acm.org/action/doSearch?AllField=' + self.current_word + '&startPage=' + str(
            self.page) + '&pageSize=20'
        yield Request(url, headers=HEADERS, callback=self.parse_result_page, dont_filter=True)

    def parse_result_page(self, response):
        result_selectors = response.xpath('//li[contains(@class,"search__item issue-item-container")]')
        for selector in result_selectors:
            paper_url = 'https://dl.acm.org' + selector.xpath('div[2]/div[2]/div/h5/span/a/@href').extract()[0]
            yield Request(url=paper_url, callback=self.parse_paper, meta={'url': paper_url}, dont_filter=True)
        self.page = self.page + 1
        if self.page >= 1:  # todo 应为100
            self.used_list.append(self.current_word)
            if len(self.candidate_list) > 0:
                self.current_word = self.candidate_list.pop()
            else:
                self.set_checkpoint()
                return
            self.page = 0
            self.set_checkpoint()
        list_url = 'https://dl.acm.org/action/doSearch?AllField=' + self.current_word + '&startPage=' + str(
            self.page) + '&pageSize=20'
        yield Request(url=list_url, callback=self.parse_result_page, headers=HEADERS, dont_filter=True)

    def set_checkpoint(self):
        checkpoint = {
            'used_list': self.used_list,
            'current_word': self.current_word,
            'candidate_list': self.candidate_list,
            'page': self.page,
        }
        set_checkpoint(ACM_CHECKPOINT_PATH, checkpoint, 'w+')

    def parse_paper(self, response):
        paper = ItemLoader(item=AcademicItem(), selector=response)

        paper.add_xpath('title', '//*[@id="pb-page-content"]/div/main/div[2]/article/div[1]/div[2]/div/div/div['
                                 '2]/h1/text()')
        paper.add_xpath('abstract', '//*[@id="pb-page-content"]/div/main/div[2]/article/div[2]/div[2]/div[2]/div['
                                    '1]/div/div[2]/p/text()')
        # 拼接为|分割的字符串，在pipeline中处理
        authors_selector = response.xpath('//span[@class="loa__author-name"]/span/text()')
        authors = ''
        for s in authors_selector:
            authors = authors + s.extract() + '|'
        paper.add_value('authors', authors)
        paper.add_xpath('doi', '//*[@id="pb-page-content"]/div/main/div[2]/article/div[1]/div[2]/div/div/div['
                               '4]/div/span[3]/a/text()')
        paper.add_value('url', response.request.meta['url'])
        paper.add_xpath('year', '//*[@id="pb-page-content"]/div/main/div[2]/article/div[1]/div[2]/div/div/div['
                                '4]/div/span[1]/span/text()')
        paper.add_xpath('month', '//*[@id="pb-page-content"]/div/main/div[2]/article/div[1]/div[2]/div/div/div['
                                 '4]/div/span[1]/span/text()')
        # 交由后续pipeline进一步判断文章类型
        paper.add_xpath('type', '//*[@id="pb-page-content"]/div/header/div[4]/div/div/nav/a[2]/@text()')
        paper.add_xpath('venue', '//*[@id="pb-page-content"]/div/main/div[2]/article/div[1]/div[2]/div/div/div['
                                 '4]/div/a/span/text()')
        paper.add_value('source', 'ACM')
        paper.add_xpath('video_url', '//*[@id="pb-page-content"]/div/main/div[2]/article/div[2]/div[2]/div[2]/div['
                                     '3]/div[2]/div/div/div/div[2]/div/div/div[2]/a[2]/@href')
        # video_path交由后续pipeline处理
        paper.add_value('video_path', 'N/A')
        paper.add_xpath('thumbnail_url', '/html/body/div[1]/div/main/div[2]/article/div[2]/div[2]/div[2]/div[3]/div['
                                         '2]/div/div/div/div[1]/div/stream/@poster')
        paper.add_xpath('pdf_url', '//*[@id="pb-page-content"]/div/main/div[2]/article/div[1]/div[2]/div/div/div['
                                   '6]/div/div[2]/ul[2]/li[2]/a/@href')
        # pdf_path交由后续pipeline处理
        paper.add_value('pdf_path', 'N/A')
        paper.add_xpath('inCitations', '//*[@id="pb-page-content"]/div/main/div[2]/article/div[1]/div[2]/div/div/div['
                                       '6]/div/div[1]/div/ul/li[1]/span/span[1]/text()')
        outCitations_selector = response.xpath('//ol[contains(@class,"rlist references__list")]/li').extract()
        paper.add_xpath('outCitations', str(len(outCitations_selector)))

        yield paper.load_item()
