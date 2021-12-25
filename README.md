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
| 张泽康 | 3120211082 | 搭建爬虫框架、负责爬取ScienceDirect                          |
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