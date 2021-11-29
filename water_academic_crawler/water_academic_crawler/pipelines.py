# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import hashlib
import re

import pymongo
from scrapy.exceptions import DropItem
from scrapy.http.request import Request
from scrapy.pipelines.files import FilesPipeline
from scrapy.utils.misc import arg_to_iter
from twisted.internet.defer import DeferredList

from water_academic_crawler.util import has_attr
from water_academic_crawler.util import get_filename


class DeduplicatePipeline(object):
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
        # 去重
        md5 = hashlib.md5(item['title'].encode(encoding='UTF-8')).hexdigest()
        query = {
            '_id': md5
        }
        cursor = self.db_collection.find(query)
        if len(list(cursor)) != 0:
            print(item['title'], 'has already existed')
            raise DropItem()
        item['_id'] = md5
        return item

    def close_spider(self, spider):
        # 关闭数据库连接
        self.db_client.close()


class DBStoragePipeline(object):
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
        # 将数据插入到集合中
        print('Crawled', item['title'])
        item_dict = dict(item)
        self.db_collection.insert_one(item_dict)
        return item


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
            try:
                item['month'] = self.get_month(month)
            except KeyError:
                item['month'] = month
            item['year'] = year

        # 判断文章类型
        if has_attr(item, 'type'):
            type_str = item['type']
            c_exp = r'((c|C)onference)|((p|P)roceeding)'
            j_exp = r'(j|J)ournal'
            if re.search(c_exp, type_str) is not None:
                item['type'] = 'conference'
            elif re.search(j_exp, type_str) is not None:
                item['type'] = 'journal'
            else:
                item['type'] = 'unknown'

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
