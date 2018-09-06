#!/usr/bin/env python
# Created on 2018-07-30 23:06:00
# Project: ChinaMobileProcurementBiddingSite

import re
import time

from pyquery import PyQuery as pq
from pyspider.libs.base_handler import *

'''
WebDAV 自动完成中文转码UTF-8？
'''


class Handler(BaseHandler):
    crawl_config = {
        "headers": {
            "User-Agent": "Mozilla/5.0 (X11;Linux x86_64) AppleWebKit/537.36 (KHTML, likeGecko) Chrome/66.0.3359.181 Safari/537.36"
        }
    }

    @every(minutes=4 * 60)
    # on_start方法每4小时执行一次
    def on_start(self):
        # 删除results
        # resultdb = connect_database("sqlite+resultdb:///data/result.db")
        # resultdb._delete(resultdb._tablename(self.project_name), '1=1')

        # noticeType=2 采购公告
        url2 = 'https://b2b.10086.cn/b2b/main/listVendorNoticeResult.html?noticeBean.noticeType=2'
        # noticeType=3 资格预审公告查询
        url3 = 'https://b2b.10086.cn/b2b/main/listVendorNoticeResult.html?noticeBean.noticeType=3'
        # 获取当前日期
        date = time.strftime("%Y-%m-%d", time.localtime())
        # 构造POST参数
        data = {
            'page.currentPage': 1,
            'page.perPageSize': 200,
            'noticeBean.sourceCH': '',
            'noticeBean.source': '',
            'noticeBean.title': '',
            'noticeBean.startDate': '2018-08-08',
            'noticeBean.endDate': date
        }
        # 用于创建一个爬取任务，url 为目标地址，callback 为抓取到数据后的回调函数
        self.crawl(url2, callback=self.index_page, method="POST", data=data)
        self.crawl(url3, callback=self.index_page, method="POST", data=data)

    @config(age=1 * 24 * 60 * 60)
    # 设置任务的有效期限，告诉scheduler这个request过期时间是1天
    def index_page(self, response):
        # 公告详情uri
        uri = "https://b2b.10086.cn/b2b/main/viewNoticeContent.html?noticeBean.id="
        # response.doc 为 pyquery 对象，用来方便地抓取返回的html文档中对应标签的数据
        print(len(response.doc("tr")))
        for each in response.doc("tr").items():
            # 过滤无效数据
            if each.attr("onclick"):
                notice_id = each.attr("onclick").split("'")[1]
                href = uri + notice_id
                if each('.  > td').length > 2:
                    purchase_unit = pq(each('.  > td')[0]).text()
                    notice_type = pq(each('.  > td')[1]).text()
                    print purchase_unit, notice_type
                self.crawl(href, callback=self.detail_page,
                           save={'purchase_unit': purchase_unit, 'notice_type': notice_type})

    @config(priority=2)
    # 设定任务优先级
    # 返回一个 dict 对象作为结果，自动保存到 resultdb
    def detail_page(self, response):

        # text = response.text.decode('utf-8')
        # result = pq(text).remove('script')

        result = response.doc.remove('script')  # 去除无效元素 script
        # print result.text()

        topics = {
            '项目名称': '解析失败',
            '招标人': '解析失败',
            '招标代理机构': '无',
            '采购内容概况': '解析失败',
            '文件售卖时间': '解析失败',
            '投标截止时间': '解析失败',
            '联系方式': '解析失败',
        }

        # 无用内容列表
        useless_topics = ['免责声明', '发布公告的媒介', '电子采购应答规则']
        # 项目概况相关主题列表
        project_overview_topics = ['项目概况与招标范围', '项目概况', '招标范围', '项目概况与招标内容', '项目概况与比选内容', '项目概况与采购范围',
                                   '采购说明', '采购内容', '采购内容及相关内容', '采购项目概况', '采购货物的名称', '采购项目的名称',
                                   '工程概况与比选内容', '比选项目的名称', ]
        # 截止日期正则表达式：'截止时间(.*)(\d+)年(\d{1,2})月(\d{1,2})日'
        deadline_pattern = re.compile(u'\u622a\u6b62\u65f6\u95f4(.*)(\d+)\u5e74(\d{1,2})\u6708(\d{1,2})\u65e5')
        # 文件售卖时间正则表达式: '文件售卖时间(.*)(\d+)年(\d{1,2})月(\d{1,2})日'
        document_sale_time_pattern = re.compile(
            u'\u6587\u4ef6\u552e\u5356\u65f6\u95f4(.*)(\\d+)\u5e74(\\d{1,2})\u6708(\\d{1,2})\u65e5')
        # 报名时间
        # 日期正则表达式: '(\d+)年(\d{1,2})月(\d{1,2})日(.*)(\d{1,2})时'
        date_pattern = re.compile(u'(\\d+)\u5e74(\\d{1,2})\u6708(\\d{1,2})\u65e5(.*)(\\d{1,2})\u65f6')
        # 无效字符字典
        useless_char = "\xa0\n\t_ "
        useless_table = {ord(char): None for char in useless_char}

        # 去除空元素
        tr_items = result('#mobanDiv > table tr').items()
        tr_items_nonzero = []
        for item in tr_items:
            # print(item('span').length)
            if item('span').length > 0:
                tr_items_nonzero.append(item)

        # !提取--URL
        topics['url'] = response.url

        # !提取--项目名称
        topics['项目名称'] = result('h1').text()

        # !提取--招标人
        last_tr = tr_items_nonzero[-1]
        last_tr_span_text = pq(pq(last_tr)('span')[0]).text()
        # print last_tr_span_text
        # u'\uff1a' = "："
        if last_tr_span_text.count('：'):
            text = last_tr_span_text.split('：')[1].translate(useless_table)
            if text.count('/'):
                topics['招标人'] = text.split("/")[0]
                topics['招标代理机构'] = text.split("/")[1]
            else:
                topics['招标人'] = text

        # !提取--采购内容概况
        for each in tr_items_nonzero:
            span_list = list(each('tr > td > span').items())
            if len(span_list) > 0:
                # u'\u3001' = '、'
                topic = span_list[0].text().split('、')[1]
                if topic in project_overview_topics:
                    print(topic)
                    topics['采购内容概况'] = pq(each).clone().remove('table')('div').text().translate(useless_table)

        # !提取--其它主题
        for each in result('#mobanDiv > table tr').items():
            span = each('tr > td > span')
            # 过滤无主题内容
            if span.length > 0:
                topic = pq(span[0]).text().split('、')[1]

                if topic not in (useless_topics + project_overview_topics):
                    print(topic)
                    len_p = each('p').length
                    len_div = each('div').length
                    # print("\n p 元素: ", len_p, "\n div 元素: ", len_div)
                    infos = []
                    items = []
                    if len_p > 0:
                        items = each('p').items()
                    else:
                        if len_div > 0:
                            items = each('div').items()

                    for item in items:
                        text = item.text()
                        if type(item.text()) == 'unicode':
                            text = text.translate(useless_table)
                        # print text
                        if len(text) > 0:
                            # !提取--投标截止时间
                            deadline = deadline_pattern.findall(text)
                            sale_time = document_sale_time_pattern.findall(text)
                            if len(deadline) > 0:
                                # print '投标截止时间', len(deadline)
                                for m in date_pattern.finditer(text):
                                    topics['投标截止时间'] = m.group()
                            if len(sale_time) > 0:
                                # print '文件售卖时间', len(sale_time)
                                for m in date_pattern.finditer(text):
                                    topics['文件售卖时间'] = m.group()
                            else:
                                infos.append(text)

                    # print(infos)
                    if topic == '联系方式':
                        topics['联系方式'] = infos
                    else:
                        topics[topic] = infos

        # 关注的招标主题
        key_words = ['综合', '代维', '无线网络', '室内', '分布', '设计院', '通信', '配套', '施工', '集客', '家客']

        return {
            '采购需求单位': response.save['purchase_unit'],
            '公告类型': response.save['notice_type'],
            "项目名称": topics['项目名称'],
            "招标人": topics['招标人'],
            "招标代理机构": topics['招标代理机构'],
            "投标截止时间": topics['投标截止时间'],
            "采购内容概况": topics['采购内容概况'],
            "文件售卖时间": topics['文件售卖时间'],
            '联系方式': topics['联系方式'],
        }