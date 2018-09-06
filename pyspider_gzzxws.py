#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Created on 2016-04-29 21:07:53
# Project: Guang_Zhou_Wen_Shi

from pyspider.libs.base_handler import *
import os
import re

DIR = '/home/peng/python/guangzhouwenshi'


class Deal():
    def __init__(self):
        self.path = DIR

    def make_dir(self, path, name):
        if path == '':
            dir_path = self.path + '/' + name
        else:
            dir_path = self.path + '/' + path + '/' + name
        exists = os.path.exists(dir_path)
        if not exists:
            os.makedirs(dir_path)
            return dir_path
        else:
            return dir_path

    def save_text(self, content, path, name):  # path是完整的
        text_path = path + '/' + name + '.txt'
        with open(text_path, 'w+') as f:
            f.write(content)

    def save_img(self, content, path, name, extension):  # path是完整的
        img_path = path + '/' + name + '.' + extension
        with open(img_path, 'w+') as f:
            f.write(content)


class Handler(BaseHandler):
    crawl_config = {
    }

    def __init__(self):
        self.deal = Deal()

    @every(minutes=24 * 60)
    def on_start(self):
        # 函数爬取的主入口：
        self.crawl('http://www.gzzxws.gov.cn/', callback=self.index_page)

        # 广州文史这一类的特殊处理：
        self.crawl('http://www.gzzxws.gov.cn/gzws/gzws/sqfl/ggkfsq/', callback=self.list_page, save='广州文史',
                   fetch_type='js')
        self.crawl('http://www.gzzxws.gov.cn/gzws/gzws/fl/zz/', callback=self.list_page, save='广州文史', fetch_type='js')

        # 党团史料这一类的特殊处理：
        self.crawl('http://www.gzzxws.gov.cn/dtsl/dpslg/zzjj2/', callback=self.list_page, save='党团史料', fetch_type='js')
        self.crawl('http://www.gzzxws.gov.cn/dtsl/zgdsg/zlsc/', callback=self.list_page, save='党团史料', fetch_type='js')
        self.crawl('http://www.gzzxws.gov.cn/dtsl/gztsg/zrsy/', callback=self.list_page, save='党团史料', fetch_type='js')

        # 专题文史这一类的特殊处理：
        self.crawl('http://www.gzzxws.gov.cn/gxsl/bngy/sy/', callback=self.list_page, save='专题文史', fetch_type='js')

        # 辛亥革命这一类的特殊处理：
        self.crawl('http://www.gzzxws.gov.cn/xhgm/gmxhgm/', callback=self.list_page, save='辛亥革命', fetch_type='js')

    @config(age=10 * 24 * 60 * 60)
    def index_page(self, response):
        for each in response.doc('.top_pad22 a').items():
            # print each.text()
            # 重点调试部分*********************************************************
            if each.attr.href != 'http://www.gzzxws.gov.cn/':
                name = each.text()
                dir_path = self.deal.make_dir('', name)
                # print dir_path
                self.crawl(each.attr.href, callback=self.detail_page, save=name, fetch_type='js')
            # *********************************************************************

    @config(priority=2)
    def detail_page(self, response):
        # print response.save

        # *******************区县文志的特殊情况********************************
        # print response.doc('.border_content tr td table tr td a').eq(0).text()
        if re.match('http://www.gzzxws.gov.cn/qxws/', response.url):
            for each in response.doc('.border_content tr td table tr td a').items():
                if each.text().encode('utf-8') == '更多>>':
                    self.crawl(each.attr.href, callback=self.list_page, fetch_type='js', save=response.save)
                    break
        # **********************************************************************

        # print each.text().encode('utf-8')
        # if each.text().encode('utf-8') == '更多>>':
        # self.crawl(each.attr.href,callback=self.list_page,fetch_type = 'js',save = response.save)

        # ***************普通情况*********************
        else:
            for each in response.doc('.border_content tr td table tr td a').items():
                # print each.text().encode('utf-8')
                if each.text().encode('utf-8') == '更多>>':
                    self.crawl(each.attr.href, callback=self.list_page, fetch_type='js', save=response.save)

        # ***************************************************

        for each in response.doc('.zt_font1').items():
            self.crawl(each.attr.href, callback=self.detail_page, fetch_type='js', save=response.save)

        # try的部分需要重点调试

    def list_page(self, response):
        # print response.save
        # .border_content table a
        # .border_content table td > a
        for each in response.doc('.border_content table td > a').items():
            # print each.attr.href
            self.crawl(each.attr.href, callback=self.finnal_page, save=response.save)

        page_num = int(response.doc('.texttext > span').eq(0).text())
        url_part = response.url.split('/')

        if re.match(r'index_', url_part[-1]):
            url_part[-1] = ''
            response.url = '/'.join(url_part)

        for i in range(1, page_num):
            url = response.url + 'index_' + str(i) + '.htm'
            self.crawl(url, callback=self.list_page, save=response.save, fetch_type='js')

        for each in response.doc('.quick_meun').items():
            list_name = each.text().encode('utf-8')
            if list_name != '视频文史' and list_name != '音频文史':
                self.crawl(each.attr.href, callback=self.list_page, save=response.save, fetch_type='js')

    def finnal_page(self, response):
        # print response.save
        name = response.doc('.border_content table td').eq(0).text()
        finnal_path = self.deal.make_dir(response.save, name)
        # print finnal_path

        # 取出图片名称、扩展名、url形成元组的列表*********************************
        sign = 0
        img_list = []
        j = 1
        text_content = ''
        # .Custom_UnionStyle > p
        # td > p
        select_list_1 = ['.Custom_UnionStyle > p', 'td > p']
        for select in select_list_1:
            for each in response.doc(select).items():
                # print 'for1 找到'
                # print each
                # print each.attr.align
                text_content = text_content + each.text()

                if sign == 1 and each.attr.align == 'center':
                    if each.text().encode('utf-8') == '':
                        # print 'heyhey'
                        general_img_name = name + str(j)
                        temp.append(general_img_name)
                        img_list.append(tuple(temp))
                        j += 1
                        sign = 0
                    else:
                        # print each.text()
                        temp.append(each.text())
                        img_list.append(tuple(temp))
                        sign = 0


                elif sign == 1:
                    general_img_name = name + str(j)
                    # print general_img_name
                    temp.append(general_img_name)
                    img_list.append(tuple(temp))
                    j += 1
                    sign = 0

                if each.find('img'):
                    temp = []
                    # print each('img').attr.src
                    temp.append(each('img').attr.src)
                    img_extension = each('img').attr.src.split('.')[-1]
                    temp.append(img_extension)
                    sign = 1

        # *******************************************************************

        # ***************因为结构异常找不到内容的处理*************************
        if text_content == '':
            # print '异常找到1'
            for each in response.doc('div > p').items():
                # print each.text()
                text_content = text_content + each.text()

        if text_content == '':
            # print '异常找到2'
            for each in response.doc('.border_content table td').items():
                if not each.find('script'):
                    text_content = text_content + each.text()

        select_list_2 = ('.Custom_UnionStyle img', 'p > img')

        if img_list == []:
            for select in select_list_2:
                for each in response.doc(select).items():
                    extension = each.attr.src.split('.')[-1]
                    general_img_name = name + str(j)
                    j += 1
                    url = each.attr.src
                    temp = [url, extension, general_img_name]
                    img_list.append(tuple(temp))

        # ********************************************************************

        # 测试用print：
        # print len(img_list)
        # print  img_list
        # print text_content

        # **************************************************

        # 保存文字:

        # 测试用print：
        # print finnal_path
        # print content
        self.deal.save_text(text_content.encode('utf-8'), finnal_path, name)

        # 保存图片********************************************
        for img in img_list:
            self.crawl(img[0], callback=self.save_img, save=[finnal_path, img])

        # ***************************************************

    def save_img(self, response):
        save_img_content = response.content
        save_img_path = response.save[0]
        save_img_name = response.save[1][2]
        save_img_extension = response.save[1][1]
        self.deal.save_img(save_img_content, save_img_path, save_img_name, save_img_extension)

        # 测试用print：
        # print save_img_name
        # print save_img_extension
        # print save_img_path
