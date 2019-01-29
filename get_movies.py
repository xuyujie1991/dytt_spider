#-*- coding:utf-8 -*-

"""
电影天堂最新电影抓取
"""

from __future__ import absolute_import
from __future__ import unicode_literals
import json
import os
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import re
import traceback
import json
import time
import logging
import datetime
import logging
import requests
from useragent import UserAgent as UA

logger = logging.getLogger(__name__)

_host = 'www.dy2018.com'
_host_url = 'https://www.dy2018.com'

logger = logging.getLogger(__name__)

class BaseSession(object):
    _timeout = 5
    _normal_status = [200]

    """ Requests会话 """
    def __init__(self, **kwargs):
        self.headers = None
        self.useragent = None
        self.session = None
        self.timeout = self._timeout if not kwargs.get('timeout') else kwargs.get('timeout')

        self.host = None if not kwargs.get('host') else kwargs.get('host')
        self.host_url = None if not kwargs.get('host_url') else kwargs.get('host_url')

        self.init_headers()

    """
        初始化请求头
    """
    def init_headers(self):
        self.headers = {
            'User-Agent':self.get_useragent(),
            'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
        }
        if self.host:
            self.headers.update({'Host':self.host})

    """
        获取UserAgent
    """
    def get_useragent(self):
        if self.useragent:
            return self.useragent
        self.set_useragent()
        return self.useragent

    """
        设置UserAgent
    """
    def set_useragent(self, ua_type=None):
        if ua_type and ua_type.strip().lower() == 'ie':
            self.useragent = UA().ie()
        elif ua_type and ua_type.strip().lower() == 'opera':
            self.useragent = UA().opera()
        elif ua_type and ua_type.strip().lower() == 'chrome':
            self.useragent = UA().chrome()
        elif ua_type and ua_type.strip().lower() == 'firefox':
            self.useragent = UA().firefox()
        elif ua_type and ua_type.strip().lower() == 'safari':
            self.useragent = UA().safari()
        else:
            self.useragent = UA().random()

    def get_session(self):
        if self.session:
            return self.session
        self.set_session()
        return self.session

    def set_session(self):
        self.session = requests.session()
        self.session.headers = self.headers

        
    '''
        requests.get
    '''
    def get(self, **options):
        if options.has_key('timeout') == False:
            options['timeout'] = self.timeout
        self.get_session()
        resp = self.session.get(**options)
        if resp.status_code not in self._normal_status:
            raise Exception("unexpected status_code:%s" %resp.status_code)
        return resp


class Session(BaseSession):
    pass

class Spider(object):
    def __init__(self):
        self.session = Session()

    def get_detail(self, url=None):
        D = {}
        resp = self.session.get(url=url)
        resp.encoding="GB2312"
        logger.info("DETAIL_STATUS:{}".format(resp.status_code))
        #内容解析,不做
        #content = self.parse_detail_content(resp.text)
        content = "content"
        if not content:
            raise Exception("content is null")
        DD = self.parse_detail_date(resp.text)
        if not DD:
            raise Exception("pdate is null")
        D['content'] = content
        D['publish_date'] = DD['publish_date']
        D['score'] = DD['score']
        D['types'] = DD['types']
        D['url'] = self.parse_detail_download(resp.text)
        D['url2'] = self.parse_detail_download2(resp.text)
        D['img_url'] = self.parse_detail_image(resp.text)

        return D

    def list_urls(self, from_idx, thru_idx):
        L = []
        for i in range(from_idx, thru_idx+1):
            if i == 1:
                url = 'https://www.dy2018.com/html/gndy/dyzz/'
            else:
                url = 'https://www.dy2018.com/html/gndy/dyzz/index_{}.html'.format(i)
            L.append(url)
        return L
        

    def get_list(self, page_from=1, page_end=1):
        L = []
        urls = self.list_urls(page_from, page_end)
        for u in urls:
            try:
                L+=self.get_list_one(url=u)
            except:
                logger.error(traceback.format_exc())
                continue
        return L

    """
    列表解析
    """
    def get_list_one(self, url=None):
        url = url
        resp = self.session.get(url=url)
        logger.info('LIST_STATUS:{}'.format(resp.status_code))
        resp.encoding = "GB2312"
        #with open('list.txt', 'w') as fp:
        #    fp.write(resp.text)
        return self.parse_list(resp.text)

    """
    #<a href="/i/99518.html" class="ulink" title="2018年美国6.6分恐怖片《寂静之地》BD中英双字">2018年美国6.6分恐怖片《寂静之地》BD中英双字</a>
    列表解析
    """
    def parse_list(self, html):
        import re
        p = re.compile(r'<a href="(.*html)"\s+class="ulink"\s+title="(.*)">.*</a>')
        L=p.findall(html)
        new_L = []
        for item in L:
            if len(item) != 2:
                continue
            d = {}
            d['url'] = "https://www.dy2018.com" + item[0]
            d['title'] = item[1]
            new_L.append(d)
        return new_L

    """
        解析内容
    """
    #<!--Content Start-->
    #<p>◎影片截图</p>
    #<div><img src="https://img.diannao1.com/d/file/html/gndy/dyzz/2018-07-26/71be61c85a3873c478933a91aefb3cf7.jpg" alt="死侍2HD韩版中英双字.mkv_thumbs_2018.07.26.21_07_05(1).jpg" width="926" height="857" /></div><!--duguPlayList Start-->
    #<!--xunleiDownList Start-->
    def parse_detail_content(self, html):
        html = html.replace('\r','\n')
        p = re.compile(r'<!--Content Start-->(.*)<!--duguPlayList Start-->', re.DOTALL)
        group = p.findall(html)
        if group:
            return group[0]+self.parse_detail_download(html)
        return None

    """
        下载地址
    """
    #<td style="WORD-WRAP: break-word" bgcolor="#fdfddf"><a href="ftp://d:d@a.dygodj8.com:12311/[电影天堂www.dy2018.com]sishi2HD韩版中英双字.mkv">ftp://d:d@a.dygodj8.com:12311/[电影天堂www.dy2018.com]sishi2HD韩版中英双字.mkv</a></td>
    def parse_detail_download(self, html):
        html = html.replace('\r','\n')
        p = re.compile(r'<a href="(ftp.{1,256}.[mkv|mp4|rmvb|3gp|flv])">', re.DOTALL)
        group = p.findall(html)
        url = "未找到下载地址"
        if group:
            url = group[0]
        return url

    def parse_detail_download2(self, html):
        html = html.replace('\r','\n')
        p = re.compile(r'(magnet.{1,120})</a>', re.DOTALL)
        group = p.findall(html)
        url = "未找到下载地址"
        if group:
            url = group[0]
        return url


    #解析图片
    #<img src="https://img.diannao1.com/d/file/html/gndy/dyzz/2018-07-26/c2c8d6ea864fdafec7827732e7b220be.jpg" alt="死侍2(1).JPG" width="518" height="768" />
    def parse_detail_image(self, html):
        html = html.replace('\r','\n')
        p = re.compile(r'<img src="(http.{40,200}.["jpg"|"png"])"', re.DOTALL)
        group = p.findall(html)
        if group:
            url = group[0]
        else:
            url = None
        return url

    """
        解析日期
    """
    #<span>评分：<strong class="rank">7.9</strong></span>    <span>类型：<a href='/1/'>喜剧片</a> / <a href='/2/'>动作片</a> / <a href='/4/'>科幻片</a> / <a href='/16/'>冒险电影</a></span>  <span class="updatetime">发布时间：2018-08-05</span>
    def parse_detail_date(self, html):
        D = {}
        html = html.replace('\r','\n')
        import re
        import json
        p = re.compile(r'<span>评分：<strong class="rank">([\d|.]*)</strong></span>\s+<span>类型：(.*)</span>\s+<span class="updatetime">发布时间：(\d{4}-\d{2}-\d{2})</span>', re.DOTALL)
        group = p.findall(html)
        item = group[0] if group else None
        if item and len(item) == 3:
            type_as = item[1]
            p2 = re.compile(r'<a href=\'/\d+/\'>([\S]*)</a>', re.DOTALL)
            types = p2.findall(type_as)
            D['publish_date'] = item[2]
            D['types'] = types
            D['score'] = item[0]
            return D
        D=self.parse_detail_date2(html)
        if D:
            return D
        return None
    #<br />◎类　　别　剧情/>动作/犯罪 <br />
    #<br />◎IMDb评分　7.3/10 from 773 users <br />
    #发布时间：2019-01-23
    def parse_detail_date2(self, html):
        D = {}
        html = html.replace('\r','\n')
        p1 = re.compile(r'◎类　　别　(.{0,20})<br />',re.DOTALL)
        p2 = re.compile(r'发布时间：(\d{4}-\d{2}-\d{2})',re.DOTALL)
        p3 = re.compile(r'评分　(\d{1}\.\d{1})',re.DOTALL)
        g1=  p1.findall(html)
        g2=  p2.findall(html)
        g3=  p3.findall(html)
        if g1:
            D['types'] = g1[0].split('\/')
        if g2:
            D['publish_date'] = g2[0]
        if g3:
            D['score'] = g3[0]
        return D
    
        

    def detail_parser(self, url=None,title=None):
        import uuid
        p=re.compile(r'i/(\d{1,10}).html')
        g=p.findall(url)
        id = g[0] if g else str(uuid.uuid4())
        try:
            d=api.get_detail(url=url)
            d['title'] = title
            d['id'] = id
            return d
        except Exception as e:
            logger.error(traceback.format_exc())
            pass
        return None

if __name__ == '__main__':
    LOG_FMT =  '%(levelname) -6s %(asctime)s  %(filename)-20s %(lineno) -5d: %(message)s'
    logging.basicConfig(level=logging.INFO, log_fmt=LOG_FMT, stream=sys.stdout)
    api = Spider()

    #先爬取需要的页面的列表信息
    L = api.get_list(page_from=1, page_end=1)
    with open('L.txt', 'w') as fp:
        for i in L:
            fp.write("{}\n".format(json.dumps(i, ensure_ascii=False)))

    #根据列表页信息爬取详情
    fp2 = open('D.txt', 'w')
    with open('L.txt', 'r') as fp:
        for line in fp:
            l = json.loads(line)
            d=api.detail_parser(url=l.get('url'), title=l.get('title'))
            if d:
                fp2.write("{}\n".format(json.dumps(d, ensure_ascii=False)))
