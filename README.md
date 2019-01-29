爬取思路:

(1)根据需要爬取的页面构造页面的URL

(2)爬取页面信息,并解析每个页面的影片列表信息[包括title,url]

(3)详情爬取,根据列表页爬取到的url进行详情页信息爬去[通过正则解析]

(4)生成的D.txt就是json格式的影片信息，可以存入数据库,并做出展示效果[本人做了一个小程序],并设置了一个定时任务,定时更新影片信息

小程序列表页:
![image](https://github.com/xuyujie1991/dytt_spider/blob/master/dytt_image.png)

