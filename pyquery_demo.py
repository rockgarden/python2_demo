# -*- coding: UTF-8 -*-
import re
import unittest
import urllib2

from pyquery import PyQuery as pq

'''
# 不建议强转
# import sys
# reload(sys)
# sys.setdefaultencoding('utf8')  # default is ascii
# python 2 要将str转unicode编码 u'中文'
'''


class QueryPyQuerySuite(unittest.TestCase):

    def test_detail_page(self):

        url = 'https://b2b.10086.cn/b2b/main/viewNoticeContent.html?noticeBean.id=478772'
        # 478023 477256 478772 478825

        page = urllib2.urlopen(url)
        text = unicode(page.read(), "utf-8")

        # 去除无效元素 script
        result = pq(text).remove('script')
        # print(result)
        topics = {
            '项目名称': '解析失败',
            '招标人': '解析失败',
            '招标代理机构': '无',
            '采购内容概况': '解析失败',
            '投标截止时间': '解析失败',
        }

        # 无用内容列表
        useless_topics = [u'免责声明', u'发布公告的媒介', u'电子采购应答规则']
        # 项目概况相关主题列表
        project_overview_topics = [u'项目概况与招标范围', u'项目概况', u'招标范围', u'项目概况与招标内容', u'项目概况与比选内容',
                                   u'采购说明', u'采购内容', u'采购内容及相关内容', u'采购项目概况', u'采购货物的名称', u'采购项目的名称',
                                   u'工程概况与比选内容', u'比选项目的名称', ]
        # 截止日期正则表达式
        # python2 '截止时间(.*)(\d+)年(\d{1,2})月(\d{1,2})日' 要转为 unicode utf-8'
        # u'\u622a\u6b62\u65f6\u95f4(.*)(\d+)\u5e74(\d{1,2})\u6708(\d{1,2})\u65e5'
        deadline_pattern = re.compile(u'截止时间(.*)(\d+)年(\d{1,2})月(\d{1,2})日')
        # 日期正则表达式
        date_pattern = re.compile(u'(\d+)年(\d{1,2})月(\d{1,2})日(.*)(\d{1,2})时')
        # 无效字符字典
        useless_char = u"\xa0\n\t_ "
        useless_table = {ord(char): None for char in useless_char}

        # 去除空元素
        tr_items = result('#mobanDiv > table tr').items()
        tr_items_nonzero = []
        for item in tr_items:
            # print(item('span').length)
            if item('span').length > 0:
                tr_items_nonzero.append(item)

        # !提取--URL
        topics['url'] = url

        # !提取--项目名称
        topics['项目名称'] = result('h1').text()

        # !提取--招标人
        last_tr = tr_items_nonzero[-1]
        last_tr_span_text = pq(pq(last_tr)('span')[0]).text()
        # print '\n', last_tr_span_text
        if last_tr_span_text.count(u"："):
            text = last_tr_span_text.split(u"：")[1].translate(useless_table)
            if text.count('/'):
                topics['招标人'] = text.split("/")[0]
                topics['招标代理机构'] = text.split("/")[1]
            else:
                topics['招标人'] = text

        # !提取--采购内容概况
        for each in tr_items_nonzero:
            span_list = list(each('tr > td > span').items())
            if len(span_list) > 0:
                topic = span_list[0].text().split(u'、')[1]
                if topic in project_overview_topics:
                    print(topic)
                    topics['采购内容概况'] = pq(each).clone().remove('table')('div').text().translate(useless_table)

        # !提取--其它主题
        for each in result('#mobanDiv > table tr').items():
            span = each('tr > td > span')
            # 过滤无主题内容
            if span.length > 0:
                topic = pq(span[0]).text().split(u'、')[1]
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
                        # text = item.text().replace(u'\xa0', "")
                        # text = "".join(item.text().split())
                        # text = re.sub(useless_char, u"", item.text())
                        text = item.text().translate(useless_table)
                        # print(text)

                        # !提取--投标截止时间
                        deadline = deadline_pattern.findall(text)
                        if len(deadline) > 0:
                            # print('投标截止时间', deadline)
                            for m in date_pattern.finditer(text):
                                topics['投标截止时间'] = m.group()
                        else:
                            infos.append(text)
                    topics[topic] = infos
                    # print(infos)

        print '\n', topics['投标截止时间'], '\n', topics['采购内容概况'], '\n', topics['招标人'], '\n', topics['项目名称']

        return {
            "项目名称": topics['项目名称'],
            "招标人": topics['招标人'],
            "投标截止时间": topics['投标截止时间'],
            "采购内容概况": topics['采购内容概况'],
        }


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(QueryPyQuerySuite))
    return suite


if __name__ == "__main__":
    unittest.TextTestRunner().run(suite())
