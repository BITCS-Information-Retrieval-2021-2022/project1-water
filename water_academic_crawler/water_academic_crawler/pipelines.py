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

from water_academic_crawler.util import has_attr, get_filename, get_month


class DeduplicatePipeline:
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
            print('"%s" has already existed' % item['title'])
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
        print('Crawled "%s"' % item['title'])
        item_dict = dict(item)
        self.db_collection.insert_one(item_dict)
        return item


class ACMPipeline:
    def process_item(self, item, spider):
        if spider.name != 'ACM':
            return item

        # 处理month和year字段
        if has_attr(item, 'year'):
            month_and_year = item['year']
            month = month_and_year.split(' ')[0]
            year = month_and_year.split(' ')[1]
            try:
                item['month'] = get_month(month)
            except KeyError:
                item['month'] = month
            item['year'] = year

        # 判断文章类型
        if has_attr(item, 'type'):
            type_str = item['type']
            c_exp = r'((c|C)onference)|((p|P)roceeding)'
            j_exp = r'((j|J)ournal)|((v|V)ol)|((c|C)ommunication)'
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


class SpringerPipeline:
    def process_item(self, item, spider):
        if spider.name != 'Springer':
            return item

        # 处理month和year字段
        if has_attr(item, 'year'):
            month_and_year = item['year']
            month = month_and_year.split(' ')[1]
            year = month_and_year.split(' ')[2]
            try:
                item['month'] = get_month(month)
            except KeyError:
                item['month'] = month
            item['year'] = year

        # 列表形式存储作者
        if has_attr(item, 'authors'):
            author_list = item['authors'].split('|')
            author_list.pop()
            item['authors'] = author_list

        # 处理type
        if has_attr(item, 'type'):
            type_str = item['type']
            c_exp = r'((c|C)onference)|((p|P)roceeding)'
            j_exp = r'((j|J)ournal)|((v|V)ol)|((c|C)ommunication)'
            if re.search(c_exp, type_str) is not None:
                item['type'] = 'conference'
            elif re.search(j_exp, type_str) is not None:
                item['type'] = 'journal'
            elif has_attr(item, 'venue'):
                type_str_venue = item['venue']
                c_exp_venue = r"((c|C)onference)|((p|P)roceeding)|'|((w|W)orkshop)|([0-9][0-9])"
                j_exp_venue = r'((j|J)ournal)|((v|V)ol)|((c|C)ommunication)|((b|B)ook)|((m|M)agazine)'
                if re.search(c_exp_venue, type_str_venue) is not None:
                    item['type'] = 'conference'
                elif re.search(j_exp_venue, type_str_venue) is not None:
                    item['type'] = 'journal'
                else:
                    item['type'] = 'conference'
            else:
                item['type'] = 'conference'

        return item


class DownloadPDFPipeline(FilesPipeline):
    def process_item(self, item, spider):
        if not has_attr(item, 'pdf_url'):
            print('"%s" doesn\'t provide a pdf url' % item['title'])
            return item
        info = self.spiderinfo
        requests = arg_to_iter(self.get_media_requests(item, info))
        dlist = [self._process_request(r, info, item) for r in requests]
        dfd = DeferredList(dlist, consumeErrors=True)
        return dfd.addCallback(self.item_completed, item, info)

    def get_media_requests(self, item, info):
        print('Trying to download pdf for "%s"...' % item['title'])
        yield Request(url=item['pdf_url'], meta={'file_names': item['title']})

    def file_path(self, request, response=None, info=None, *, item=None):
        file_name = request.meta['file_names']
        return 'pdf/' + get_filename(file_name, '.pdf')

    def item_completed(self, results, item, info):
        if results[0][0]:
            file_name = item['title']
            print('Downloaded pdf for "%s"' % file_name)
            item['pdf_path'] = 'storage/pdf/' + get_filename(file_name, '.pdf')
        return item


class DownloadVideoPipeline(FilesPipeline):
    def process_item(self, item, spider):
        if not has_attr(item, 'video_url'):
            print('"%s" doesn\'t provide a video url' % item['title'])
            return item
        info = self.spiderinfo
        requests = arg_to_iter(self.get_media_requests(item, info))
        dlist = [self._process_request(r, info, item) for r in requests]
        dfd = DeferredList(dlist, consumeErrors=True)
        return dfd.addCallback(self.item_completed, item, info)

    def get_media_requests(self, item, info):
        print('Trying to download video for "%s"...' % item['title'])
        yield Request(url=item['video_url'], meta={'file_names': item['title']})

    def file_path(self, request, response=None, info=None, *, item=None):
        file_name = request.meta['file_names']
        return 'video/' + get_filename(file_name, '.mp4')

    def item_completed(self, results, item, info):
        if results[0][0]:
            file_name = item['title']
            print('Downloaded video for "%s"' % file_name)
            item['video_path'] = 'storage/video/' + get_filename(file_name, '.mp4')
        return item
