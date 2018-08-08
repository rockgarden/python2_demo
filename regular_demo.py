# -*- coding: UTF-8 -*-
import re

# python 2 要设定编码
import sys
import unittest

from pip._vendor import chardet

reload(sys)
sys.setdefaultencoding('utf8')


class RegularSuite(unittest.TestCase):

    def test_detail_page(self):
        re.sub(ur'.*[\u4E00-\u9FA5]+.*', '', unicode('中文'))
        epre = re.compile(r"[\s\w]+")
        chre = re.compile(ur".*[\u4E00-\u9FA5]+.*")
        jpre = re.compile(ur".*[\u3040-\u30FF\u31F0-\u31FF]+.*")
        hgre = re.compile(ur".*[\u1100-\u11FF\u3130-\u318F\uAC00-\uD7AF]+.*")

        x = '中文'
        defaultEncoding = sys.getdefaultencoding()
        infoencode = chardet.detect(x).get('encoding', defaultEncoding)

        print(x.decode(infoencode, 'ignore').encode('utf-8'))

    def autoTransformEncoding(self, x):
        if (x == None or x == ''):
            return ''
        defaultEncoding = sys.getdefaultencoding()
        infoencode = chardet.detect(x).get('encoding', defaultEncoding)
        if (infoencode == None):
            infoencode = defaultEncoding
            return x.decode(infoencode, 'ignore').encode('utf-8')

    def test_default_encoding(self):
        print(self.autoTransformEncoding('中文'))

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(RegularSuite))
    return suite


if __name__ == "__main__":
    unittest.TextTestRunner().run(suite())
