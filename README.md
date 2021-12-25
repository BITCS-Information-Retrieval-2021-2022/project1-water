# Project 1 - Water Academic Crawler

 ![](https://img.shields.io/badge/python-3.x-blue) ![](https://img.shields.io/badge/flake8-pass-green)

本项目实现了一个学术网站爬虫，支持爬取[ACM Digital Library](https://dl.acm.org/) 、[SpringerLink](https://link.springer.com/) 和[ScienceDirect](https://www.sciencedirect.com/) 的论文数据并下载论文pdf及视频附件（如果提供），提供可视化界面供用户查询。

## 爬虫部分

### 功能

1. 爬取三种数据源的论文数据并下载论文pdf及视频附件（如果提供）
2. 将论文数据存储到MongoDB中，字段定义如下：

|     字段名     |                含义                |      类型      |
| :------------: | :--------------------------------: | :------------: |
|     title      |              论文标题              |     字符串     |
|    abstract    |              论文摘要              |     字符串     |
|    authors     |              作者列表              |   字符串列表   |
|      doi       |              论文doi               |     字符串     |
|      url       |              论文主页              |     字符串     |
|      year      |            论文发表年份            |     字符串     |
|     month      |            论文发表月份            |     字符串     |
|      type      | "conference"、"journal"或"unknown" |     字符串     |
|     venue      |          会议或期刊的名称          |     字符串     |
|     source     |               数据源               | **字符串列表** |
|   video_url    |          视频在线播放链接          |     字符串     |
| ~~video_path~~ |   ~~视频下载到本地后的文件路径~~   |   ~~字符串~~   |
| thumbnail_url  |           视频缩略图链接           |     字符串     |
|    pdf_url     |              PDF链接               |     字符串     |
|    pdf_path    |     PDF下载到本地后的文件路径      |     字符串     |
|  inCitations   |         该论文被引用的数量         |     字符串     |
|  outCitations  |       该论文所引用的论文数量       |     字符串     |

3. 针对多个数据源中重复的论文，将其合并为一条数据，补全其他数据源中可能缺少的字段
4. 支持增量式爬取
5. 针对三种数据源设计相应规则，保证爬取结果不重不漏
6. 利用Scrapy框架自身多线程技术、数据源提供的API等手段提高爬虫效率
7. 支持通过代理方式抵御网站反爬手段
8. 设置检查点，支持断点续爬
9. 实时展示爬取进度

### 依赖项

| 软件/库 |  版本  |
| :-----: | :----: |
| python  |  3.10  |
| MongoDB | 5.0.3  |
| Scrpay  | 2.5.1  |
| pymongo | 3.12.1 |

### 使用方法

1. 安装必备软件及依赖项

```bash
pip install scrapy==2.5.1
pip install pymongo==3.12.1
```

2. 建立本地存储目录

参照`storage_example`结构建立`storage`目录

3. 编辑配置文件

- 有关数据库及其他项目参数的配置参见`/water_academic_crawler/water_academic_crawler/settings.py`中各配置项
- 有关任务进度的配置请参见`/storage_example/checkpoints`下各文件

4. 启动爬虫

```bash
cd water_academic_crawler

# source的取值应为`ACM`、`Springer`或`ScienceDirect`之一
scrapy crawl <source> -s JOBDIR=../storage/<source>
```

5. 停止爬虫

- 达到设定的终止条件爬虫自动终止
- 两次输入`Ctrl+C`可强制停止，重新输入启动命令可断点续爬

### 部分功能介绍

1. 数据结构
- 爬取到的数据结构示例如下
```json
{
"_id":"d6c904b5e7842672b974f1a159ea31d9",
"title":"Who's In Control? On Security Risks of Disjointed IoT Device Management Channels",
"abstract":"...",
"authors":["Yan Jia","Bin Yuan","Luyi Xing","Dongfang Zhao","Yifan Zhang","XiaoFeng Wang","Yijing Liu","Kaimin Zheng","Peyton Crnjak","Yuqing Zhang","Deqing Zou","Hai Jin"],
"doi":"https://doi/10.1145/3460120.3484592",
"url":"https://dl.acm.org/doi/10.1145/3460120.3484592",
"year":"2021",
"month":"11",
"type":"conference",
"venue":"CCS '21: Proceedings of the 2021 ACM SIGSAC Conference on Computer and Communications Security",
"source":["ACM"],
"video_url":"https://dl.acm.org/action/downloadSupplement?doi=10.1145%2F3460120.3484592&file=CCS21-fp326.mp4",
"thumbnail_url":"https://videodelivery.net/eyJraWQiOiI3YjgzNTg3NDZlNWJmNDM0MjY5YzEwZTYwMDg0ZjViYiIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiI2NTU1Yjg2ZmI0NGJhZjQ1MjIyNDFhMmNlNzI0OTA2YSIsImtpZCI6IjdiODM1ODc0NmU1YmY0MzQyNjljMTBlNjAwODRmNWJiIiwiZXhwIjoxNjM4MzA1NzQ1fQ.uZj7i7RIiySy5Avp0EYvDmEF9kdBqVrLzG_IfQYMGN5VtQN0mYCvjsuB7eHSnNVjPe1jF8PfByqECcW6S4OsbJ0qdjzkdWF0c9Uj7ew4gp-yT4pJQ7Eciywy2J-Geon5J53RYw1lQacQT2SohnKZ7KzsLD8m5Kfy9g85aUuseVEbKckEpvwWY0mkPEaPdB0WAwK46wbEELnNdsOuXErRpff9C-pRObbwU1CrK3c-5HEFvsr8vHnDVkhzuXfDBrkSekhPqwefH6djpvyjl-OemfzKhjlybVgJXuZ6qJE-BBPXLPfwJNudOf_a1TBEd59HSaZoVCBYxEBfv8zifyIk6g/thumbnails/thumbnail.jpg?time=10.0s",
"pdf_url":"https://dl.acm.org/doi/pdf/10.1145/3460120.3484592",
"pdf_path":"storage/pdf/Whos_In_Control_On_Security_Risks_of_Disjointed_IoT_Device_Management_Channels.pdf",
"inCitations":"0",
"outCitations":"72"
}
```
2. 低耦合的爬虫框架
- 本工程绝大多数功能特性通过重写`scrapy`框架中的`pipeline`或`middleware`实现，事实上本工程中三个爬虫也完全使用同一套框架，尽可能保持了可复用与灵活性，故如果想为该爬虫框架添加新的数据源，只需要重写`spider`的prase方法和容器`item`即可。
3. 启发式搜索策略
部分并不提供按会议（期刊）分割的论文列表的数据库或资源获取途径（如`ScienceDirect API`），需要提供关键词对于数据库进行检索，故关键词的选择策略会对爬取到内容的质量产生较大的影响，在本工程中，通过设置关键词对论文题名进行检索，可以将该爬虫爬取的问题规约到图搜索问题，其中节点为论文信息。设计启发式搜索方式如下：
- 初始化一个较为有代表性的关键词（如Transformer、Covid-19、Cell）等等，对数据库进行检索；
- 对检索到的论文题目进行分词处理，去除无意义的助词（如A、the、of）等建立优先队列，优先关键字为词语出现的次数；
- 对优先队列中的关键词有以下两种考量：
	* 如果一个词语出现的频率越高，说明词语与当前检索的关键词关系越密切，对于该关键词进行搜索的结果大多会和当前的搜索结果相关，是对当前知识领域的纵向挖掘过程；
	* 如果一个词语出现的频率低，说明词语与当前检索关键词关系不大，对于该关键词进行搜索的结果更可能和当前的搜索结果完全不同，是对知识领域之间的横向扩展过程；
- 故需要对以上两者进行衡量，来选择一个兼顾深度与广度的爬取策略，在本工程中，选择超参数λ = 0.1 ，即在选择下一个关键词时有0.9的概率选择当前优先队列中队头的关键词，进行深度挖掘，有0.1的概率选择当前优先队列中队尾的关键词


### 运行截图

![crawler-running](https://s2.loli.net/2021/12/25/6a35OR4CNYjTWSx.jpg)

![crawler-pdf](https://s2.loli.net/2021/12/25/KS3vPEzZFmCpXQL.jpg)

## 可视化界面部分

### 功能

1.Discover

- KQL(kibana查询语言)查询

- 基于条件筛选

2.Dashboard展示

### 依赖开源框架

|                           软件/库                            |  版本  |
| :----------------------------------------------------------: | :----: |
| **[elasticsearch](https://github.com/elastic/elasticsearch)** | 7.15.1 |
|       **[ kibana](https://github.com/elastic/kibana)**       | 7.15.1 |
|     **[monstache](https://github.com/rwynn/monstache)**      |  6.77  |

### 使用方法

1. 连接北理工**校园网**
2. 打开浏览器，访问`http://10.108.21.50:5601/`
3. 按需浏览、自定义查询范围

### 运行截图

1.Discover

- KQL

  ![Discover-KQL](https://s2.loli.net/2021/12/25/uwgGQ86lxpqFDOo.png)

- 筛选

  ![Discover-Filter](https://s2.loli.net/2021/12/25/1aCIjmNPkthisA3.png)

2.Dashboard

![dashboard1](https://s2.loli.net/2021/12/25/waMD7ZYjs3Q9mxd.png)

![dashboard2](https://s2.loli.net/2021/12/25/lbdCoRaL7WtAvVH.png)

![dashboard3](https://s2.loli.net/2021/12/25/SH2ebfnrv3L64kQ.png)

![dashboard4](https://s2.loli.net/2021/12/25/yiEJ8UOlcHrWxCw.png)

## 项目结构

```
project1-water
│  .gitignore  # 指定不需要添加到版本管理中
│  README.md  # 项目README
│  
├─images  # README中的使用的图像
│      
├─storage-example  # 示例
│  │  SpringerSubDiscipline.txt  # Springer Link中待爬取的关键词列表
│  │  
│  ├─checkpoints  # 检查点，记录各任务当前进展
│  │      ACM.json  # ACM Digital Library
│  │      ScienceDirect.json  # ScienceDirect
│  │      Springer.json  # Springer Link
│  │      
│  ├─pdf  # 下载的pdf将位于本目录
│  │      
│  └─video  # 下载的视频将位于本目录
│          
└─water_academic_crawler  ##爬虫项目
    │  scrapy.cfg
    │  
    └─water_academic_crawler
        │  items.py  # 定义存储爬取到的数据的容器
        │  middlewares.py  # 包含下载器中间件和爬虫中间件模型的代码
        │  pipelines.py  # 管道组件的代码
        │  settings.py  # 爬虫项目的设置文件
        │  util.py  # 项目中用到的工具方法
        │  __init__.py
        │  
        ├─proxy
        │      proxy.json  # 代理列表
        │      
        ├─spiders  # 爬虫
        │  │  ACM.py  # ACM Digital Library
        │  │  CrawlProxy.py  # 爬取代理服务器地址
        │  │  ScienceDirect.py  # ScienceDirect
        │  │  Springer.py  # Springer Link
        │  │  __init__.py
        │  │  
        │  └─__pycache__
        │          ...
        │          
        └─__pycache__
                ...
```

## 成员分工

|  姓名  |    学号    | 分工                                                         |
| :----: | :--------: | :----------------------------------------------------------- |
|  顾骁  | 3120211034 | 组长。参与搭建前端框架、参与爬取SpringerLink、撰写文档       |
| 朱长昊 | 3120211053 | 搭建爬虫框架、负责爬取ACM Digital Library和SpringerLink、撰写文档 |
| 王华章 | 3120211044 | 分析网页框架、参与爬取ACM Digital Library                    |
|  黄鹏  | 3120211036 | 分析网页框架、参与爬取ACM Digital Library                    |
| 张泽康 | 3120211082 | 搭建爬虫框架、负责爬取ScienceDirect、撰写文档                          |
| 赵山博 | 3120210999 | 负责搭建前端框架、参与爬取ACM Digital Library                |
| 陈姣玉 | 3520210067 | 参与爬取ACM Digital Library                                  |

## 成果总结
- 论文总数 4,848,967
  - ScienceDirect 3,312,967
  - Springer 1,281,058
  - ACM 261,284
- 下载pdf
  - 89,913篇
  - 117 GB
- 字段覆盖率
  - ScienceDirect无摘要
  - 其余两数据源全覆盖