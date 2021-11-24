# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import hashlib
from urllib import request

import pymongo
from scrapy.exceptions import DropItem


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
        print('DBStoragePipeline', item)

        # 去重
        md5 = hashlib.md5(item['title'].encode(encoding='UTF-8')).hexdigest()
        query = {
            '_id': md5
        }
        cursor = self.db_collection.find(query)
        if len(list(cursor)) != 0:
            raise DropItem("查找到重复论文: %s" % item)

        # 下载pdf
        # request.urlretrieve(item['video_url'], filename='./' + md5 + '.mp4')

        # 将数据插入到集合中
        item['_id'] = md5
        item_dict = dict(item)
        self.db_collection.insert_one(item_dict)
        return item

    def close_spider(self, spider):
        # 关闭数据库连接
        self.db_client.close()


class ACMPipeline:
    def process_item(self, item, spider):
        if spider.name != 'ACM':
            return item

        print('ACMPipeline', item)

        # 处理month和year字段
        month_and_year = item['year']
        month = month_and_year.split(' ')[0]
        year = month_and_year.split(' ')[1]
        item['month'] = month
        item['year'] = year

        # todo 如果获取不到相应key会报错，考虑用try？
        # 拼接url
        # item['pdf_url'] = 'https://dl.acm.org' + item['pdf_url']
        item['video_url'] = 'https://dl.acm.org' + item['video_url']

        return item
