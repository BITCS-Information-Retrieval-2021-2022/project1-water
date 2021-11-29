# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import hashlib

import pymongo
from scrapy.exceptions import DropItem
from scrapy.http.request import Request
from scrapy.pipelines.files import FilesPipeline
from scrapy.utils.misc import arg_to_iter
from twisted.internet.defer import DeferredList

from water_academic_crawler.items import PDFItem
from water_academic_crawler.settings import HEADERS_EXAMPLE

from water_academic_crawler.util import has_attr
from water_academic_crawler.util import get_filename


class WaterAcademicCrawlerPipeline:
    def process_item(self, item, spider):
        return item


class DBStoragePipeline(object):
    # Spider开启时，获取数据库配置信息，连接MongoDB数据库服务器
    def open_spider(self, spider):
        # 获取配置文件中MongoDB配置信息
        host = spider.settings.get("MONGODB_HOST")
        port = spider.settings.get("MONGODB_PORT")
        db_name = spider.settings.get("MONGODB_NAME")
        collection_name = spider.settings.get("MONGODB_COLLECTION")
        # 连接数据库
        self.db_client = pymongo.MongoClient(host=host, port=port)
        self.db = self.db_client[db_name]
        self.db_collection = self.db[collection_name]

    def process_item(self, item, spider):
        if isinstance(item, PDFItem):
            return item

        # 去重
        md5 = hashlib.md5(item['title'].encode(encoding='UTF-8')).hexdigest()
        query = {
            '_id': md5
        }
        cursor = self.db_collection.find(query)
        if len(list(cursor)) != 0:
            print("查找到重复论文: %s" % item['title'])
            raise DropItem("查找到重复论文: %s" % item['title'])

        # 将数据插入到集合中
        item['_id'] = md5
        item_dict = dict(item)
        self.db_collection.insert_one(item_dict)
        return item

    def close_spider(self, spider):
        # 关闭数据库连接
        self.db_client.close()


class ACMPipeline:
    def get_month(self, mon):
        month_dict = {
            'January': '01',
            'February': '02',
            'March': '03',
            'April': '04',
            'May': '05',
            'June': '06',
            'July': '07',
            'August': '08',
            'September': '09',
            'October': '10',
            'November': '11',
            'December': '12'
        }
        return month_dict[mon]

    def process_item(self, item, spider):
        if spider.name != 'ACM':
            return item

        # 处理month和year字段
        if has_attr(item, 'year'):
            month_and_year = item['year']
            month = month_and_year.split(' ')[0]
            year = month_and_year.split(' ')[1]
            item['month'] = self.get_month(month)
            item['year'] = year

        # 列表形式存储作者
        if has_attr(item, 'authors'):
            author_list = item['authors'].split('|')
            author_list.pop()
            item['authors'] = author_list

        # 拼接url
        if has_attr(item, 'pdf_url'):
            item['pdf_url'] = 'https://dl.acm.org' + item['pdf_url']
        if has_attr(item, 'video_url'):
            item['video_url'] = 'https://dl.acm.org' + item['video_url']

        return item


class DownloadPDFPipeline(FilesPipeline):
    def process_item(self, item, spider):
        if not has_attr(item, 'pdf_url'):
            print(item['title'], "doesn't provide pdf url")
            return item
        info = self.spiderinfo
        requests = arg_to_iter(self.get_media_requests(item, info))
        dlist = [self._process_request(r, info, item) for r in requests]
        dfd = DeferredList(dlist, consumeErrors=True)
        return dfd.addCallback(self.item_completed, item, info)

    def get_media_requests(self, item, info):
        print('Trying to download pdf...')
        yield Request(url=item['pdf_url'], meta={'file_names': item['title']})

    def file_path(self, request, response=None, info=None, *, item=None):
        file_name = request.meta['file_names']
        return 'pdf/' + get_filename(file_name, '.pdf')

    def item_completed(self, results, item, info):
        if results[0][0]:
            file_name = item['title']
            print('Downloaded pdf for', file_name)
            item['pdf_path'] = 'storage/pdf/' + get_filename(file_name, '.pdf')
        return item


class DownloadVideoPipeline(FilesPipeline):
    def process_item(self, item, spider):
        if not has_attr(item, 'video_url'):
            print(item['title'], "doesn't provide video url")
            return item
        info = self.spiderinfo
        requests = arg_to_iter(self.get_media_requests(item, info))
        dlist = [self._process_request(r, info, item) for r in requests]
        dfd = DeferredList(dlist, consumeErrors=True)
        return dfd.addCallback(self.item_completed, item, info)

    def get_media_requests(self, item, info):
        print('Trying to download video...')
        yield Request(url=item['video_url'], meta={'file_names': item['title']})

    def file_path(self, request, response=None, info=None, *, item=None):
        file_name = request.meta['file_names']
        return 'video/' + get_filename(file_name, '.mp4')

    def item_completed(self, results, item, info):
        if results[0][0]:
            file_name = item['title']
            print('Downloaded video for', file_name)
            item['video_path'] = 'storage/video/' + get_filename(file_name, '.mp4')
        return item


class PDFPipeline(FilesPipeline):
    def get_media_requests(self, item, info):
        if isinstance(item, PDFItem):
            yield Request(url=item['file_urls'],
                          headers=HEADERS_EXAMPLE,
                          meta={'file_names': item['file_names']})

    def file_path(self, request, response=None, info=None, *, item=None):
        file_name = request.meta['file_names']
        # file_name = re.sub(r'Session\s*\w+\s*-\s*', '', file_name)
        # file_name = re.sub(r'SIGIR\s*\w*\s*-\s*', '', file_name)
        # file_name = re.sub(r'\[[\x00-\x7F]+]\s*', '', file_name)  # 去掉中括号
        # file_name = re.sub(r'(\([\x00-\x7F]*\))', '', file_name)  # 去掉小括号
        # file_name = file_name.strip()
        # file_name = re.sub(r'[\s\-]+', '_', file_name)  # 空格和连接符转化为_
        # file_name = re.sub(r'_*\W', '', file_name)  # 去掉所有奇怪的字符
        return file_name + '.pdf'

    def item_completed(self, results, item, info):
        if isinstance(item, PDFItem):
            print(results, item['file_urls'])
        return item
