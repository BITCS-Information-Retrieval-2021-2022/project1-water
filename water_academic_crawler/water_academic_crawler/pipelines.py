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


class ACMPipeline:
    def process_item(self, item, spider):
        if spider.name != 'ACM':
            return item

        # 处理month和year字段
        if has_attr(item, 'year'):
            date = item['year'].split(' ')
            month, year = '__N/A__', '__N/A__'
            if len(date) == 2:
                month = date[0]
                year = date[1]
            if len(date) == 3:
                month = date[1]
                year = date[2]
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
                del item['type']

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

        # 处理outCitations
        if has_attr(item, 'outCitations'):
            s = item['outCitations']
            if s.find('.0') > 0:
                item['outCitations'] = s[:-2]

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

        # 处理outCitations
        if has_attr(item, 'outCitations'):
            s = item['outCitations']
            if s.find('.0') > 0:
                item['outCitations'] = s[:-2]

        return item


class ScienceDirectPipeline:
    def process_item(self, item, spider):
        if spider.name != 'ScienceDirect':
            return item


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
        md5 = hashlib.md5(item['title'].encode(encoding='UTF-8')).hexdigest()
        query = {'_id': md5}
        docs = list(self.db_collection.find(query))

        # 没有重复
        if len(docs) == 0:
            item['_id'] = md5
            item['source'] = [item['source']]
            return item

        # 重复了
        print('"%s" has already existed' % item['title'])
        existed = docs[0]

        # 同一站点内重复，直接终止
        if existed['source'].count(item['source']) > 0:
            pass
        # 不同站点，更新source及其他不全的信息
        else:
            to_update = {}
            existed['source'].append(item['source'])
            to_update['source'] = existed['source']
            for key in item:
                if (not has_attr(existed, key)) and item[key] != '__N/A__':
                    to_update[key] = item[key]
            self.db_collection.update({'_id': md5}, {'$set': to_update})
            print('Updated "%s" for "%s"' % (to_update, item['title']))

            # 当前爬取ACM、可以下载pdf、之前没下载成功 的情况下，重启下载
            if spider.name == 'ACM' and has_attr(item, 'pdf_url') and (not has_attr(existed, 'pdf_path')):
                # to_update['pdf_path'] = 'storage/pdf/' + get_filename(item['title'], '.pdf')
                item['_id'] = md5
                item['drop_pdf_flag'] = True
                return item

        # 丢弃当前item
        raise DropItem()

    def close_spider(self, spider):
        # 关闭数据库连接
        self.db_client.close()


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
        # 更新下载信息（仅在重启pdf下载的情况下有效）
        if has_attr(item, 'drop_pdf_flag'):
            to_update = {'pdf_path': item['pdf_path']}
            self.db_collection.update({'_id': item['_id']}, {'$set': to_update})
            print('Updated "%s" for "%s"' % (to_update, item['title']))
            return item

        # 处理__N/A__标记
        item_dict = dict(item)
        to_delete = []
        for k in item_dict:
            if item_dict[k] == '__N/A__':
                to_delete.append(k)
        for k in to_delete:
            del item_dict[k]

        # 将数据插入到集合中
        print('Crawled "%s"' % item['title'])
        self.db_collection.insert_one(item_dict)
        return item
