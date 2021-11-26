# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from itemloaders.processors import TakeFirst


class AcademicItem(scrapy.Item):
    # 论文标题
    title = scrapy.Field(output_processor=TakeFirst())
    # 论文摘要
    abstract = scrapy.Field(output_processor=TakeFirst())
    # 作者列表
    authors = scrapy.Field(output_processor=TakeFirst())
    # 论文doi
    doi = scrapy.Field(output_processor=TakeFirst())
    # 论文主页
    url = scrapy.Field(output_processor=TakeFirst())
    # 论文发表年份
    year = scrapy.Field(output_processor=TakeFirst())
    # 论文发表月份
    month = scrapy.Field(output_processor=TakeFirst())
    # 论文类型，只有2种值"conference"或"journal"
    type = scrapy.Field(output_processor=TakeFirst())
    # 会议或期刊的名称
    venue = scrapy.Field(output_processor=TakeFirst())
    # 数据源，例如ACM，Springer
    source = scrapy.Field(output_processor=TakeFirst())
    # 视频在线播放链接
    video_url = scrapy.Field(output_processor=TakeFirst())
    # 视频下载到本地后的文件路径
    video_path = scrapy.Field(output_processor=TakeFirst())
    # 视频缩略图链接
    thumbnail_url = scrapy.Field(output_processor=TakeFirst())
    # PDF链接
    pdf_url = scrapy.Field(output_processor=TakeFirst())
    # PDF下载到本地后的文件路径
    pdf_path = scrapy.Field(output_processor=TakeFirst())
    # 该论文被引用的数量
    inCitations = scrapy.Field(output_processor=TakeFirst())
    # 该论文所引用的论文数量
    outCitations = scrapy.Field(output_processor=TakeFirst())

    # MongoDB主键
    _id = scrapy.Field()

class PDFItem(scrapy.Item):
    file_urls = scrapy.Field()
    files = scrapy.Field()
    file_names = scrapy.Field()