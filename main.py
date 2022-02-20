import queue
import threading
import requests
from bs4 import BeautifulSoup
import time
import re
import os
import yaml
import random
    
def load_config(path):
  f = open(path, 'r', encoding='utf-8')
  ystr = f.read()
  ymllist = yaml.load(ystr, Loader=yaml.FullLoader)
  return ymllist

# 反反爬虫
def getRandUa():
  first_num = random.randint(55, 62)
  third_num = random.randint(0, 3200)
  fourth_num = random.randint(0, 140)
  os_type = [
      '(Windows NT 6.1; WOW64)', '(Windows NT 10.0; WOW64)', '(X11; Linux x86_64)',
      '(Macintosh; Intel Mac OS X 10_12_6)'
  ]
  chrome_version = 'Chrome/{}.0.{}.{}'.format(first_num, third_num, fourth_num)

  ua = ' '.join(['Mozilla/5.0', random.choice(os_type), 'AppleWebKit/537.36',
                  '(KHTML, like Gecko)', chrome_version, 'Safari/537.36']
                )
  return ua

def get_data(link):
  # print('正在获取数据...')
  # print('链接：', link)
  result = ''
  header = {
    'User-Agent': getRandUa(),
    "Connection": "close",
    }
  try:
    requests.adapters.DEFAULT_RETRIES = 55
    s = requests.session()
    s.keep_alive = False # 关闭多余连接
    r = s.get(link, headers=header, timeout=120,verify=True)
    s.close()
    r.encoding = 'utf-8'
    result = r.text.encode("gbk", 'ignore').decode('gbk', 'ignore')
    if str(r) == '<Response [404]>':
      # print('<Response [404]>')
      result = ''
  except Exception as e:
    error_line = e.__traceback__.tb_lineno
    error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(e))
    print(error_info)
    result = ''
  return result


def dfs_route(route_config, path):
  for key, value in route_config.items():
    if isinstance(value, dict):
      dfs_route(value, path + [key])
    else:
      dir="/"+"/".join(path+[key])
      try:
        os.makedirs('source/_posts/' + dir + '/')
      except Exception as e:
        print('已存在目录', 'source/_posts/' + dir + '/')
      it = {'path': value, 'cat': path + [key], 'tag': path + [key], 'dir': dir}
      print(it)
      data.append(it)

md_temple = '''---
title: {title}
categories: {cat}
tags: {tag}
date: {date}
cover: {img}
comments: false
---

<div>
{text}
</div>

<div>
<!-- tag_link -->
</div>

'''

def get_post(res,item):
  cat = item['cat']
  tag = item['tag']
  dir = item['dir']
  soup = BeautifulSoup(res, ["lxml", "xml"])
  for i in soup.find_all(['item','entry'])[0:15]:
    title = ''
    text = ''
    pubdate = ''
    img = ''
    link = ''
    for child in i.children:
      childName = child.name
      if str(type(childName)) == "<class 'str'>":
        childName = str.lower(childName)
      if (childName == 'title'):
        title = child.string
      if (childName == 'description' or childName == 'content' or (text=="" and childName == 'summary')):
        text = child.string
        soup_item = BeautifulSoup(text, 'html.parser')
        if soup_item.find('img'):
          if 'data-lazy-src' in soup_item.find('img'):
            img = soup_item.find('img')['data-lazy-src'].strip()
          else:
            img = soup_item.find('img')['src'].strip()
      if (childName == 'link'):
        if "href" in child.attrs:
          link = child["href"]
        else:
          link = child.string
      if (pubdate == ''):
        pubdate = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
      if pubdate == '' and (childName == 'lastbuilddate'):
        pubdate = child.string
      if (childName == 'pubdate'):
        pubdate = child.string
      if (childName == 'updated'):
        pubdate = child.string
      if (childName == 'published'):
        pubdate = child.string

        
    # print(title)
    title = re.sub(r'[:/\\?\*“”\'"<>\.|\[\]]', '_', title)
    print(link)
    if link:
      from urllib.parse import urlparse
      url = urlparse(link)
      loc = url.scheme+"://"+url.netloc
      # 反防盗链 cors
      text = text.replace('src="https://','src="https://cors.mhuig.top/?r='+loc+'&url=https://')
      text = text.replace('="/','="https://cors.mhuig.top/?r='+loc+'&url='+loc+'/')
      text = text.replace('="../','="https://cors.mhuig.top/?r='+loc+'&url='+loc+'/../')
      if img:
        print(img)
        img = img.replace('https://','https://cors.mhuig.top/?r='+loc+'&url=https://')
        img = img.replace('http://','https://cors.mhuig.top/?r='+loc+'&url=https://')
        img = re.compile(r'^\/').sub('https://cors.mhuig.top/?r='+loc+'&url='+loc+'/', img, 1)
        img = img.replace('../','https://cors.mhuig.top/?r='+loc+'&url='+loc+'/../',1)
    if img:
      img = img.replace('http://','https://cors.mhuig.top/?url=https://')
    else:
      img = 'https://picsum.photos/400/300?random='+ str(random.randint(0,10000))
    md_content = md_temple
    try:
      with open('source/_posts/' + dir + '/' + title.replace('\n', '').replace('#', '').replace('.','') + '.md',
        mode='w',
        encoding='utf-8') as f:
        if "'" in title:
          title = '"' + title + '"'
        else:
          title = "'" + title + "'"
        md_content = md_content.format(title=title, cat=cat, tag=tag, date=pubdate, text=text, img=img)
        md_content = md_content.replace('{', '&#123;')
        md_content = md_content.replace('}', '&#125;')
        # print(link)
        md_content = md_content.replace('<!-- tag_link -->', '{% link '+str(link)+' '+str(title)+' %}')
        print('---------------------------')
        print('发布时间：', pubdate)
        print('标题：', title)
        print('描述：', '已获取内容'+text[0:20])
        print('图片：', img)
        print('---------------------------')
        f.write(md_content)
        f.close()
    except Exception as e:
      error_line = e.__traceback__.tb_lineno
      error_info = '第{error_line}行发生error为: {e}'.format(error_line=error_line, e=str(e))
      print(error_info)




# 解析线程类
class Parse(threading.Thread):
  def __init__(self, number, data_list, req_thread):
    super(Parse, self).__init__()
    self.number = number
    self.data_list = data_list
    self.req_thread = req_thread
    self.is_parse = True  # 判断是否从数据队列里提取数据

  def run(self):
    print('启动%d号解析线程' % self.number)
    while True:
      # 如何判断解析线程的结束条件
      for t in self.req_thread:
        if t.is_alive():
          break
      else:
        if self.data_list.qsize() == 0:
          self.is_parse = False

      if self.is_parse:  # 解析
        try:
          data = self.data_list.get(timeout=3)
        except Exception as e:
          data = None
        if data is not None:
          self.parse(data)
      else:
        break
    print('退出%d号解析线程' % self.number)

  # 页面解析函数
  def parse(self, data):
    get_post(data[0], data[1]) # [response,item]


# 采集线程类
class Crawl(threading.Thread):
  def __init__(self, number, req_list, data_list):
    super(Crawl, self).__init__()
    self.number = number
    self.req_list = req_list
    self.data_list = data_list

  def run(self):
    print('启动采集线程%d号' % self.number)
    while self.req_list.qsize() > 0:
      item = self.req_list.get()
      print('%d号线程采集：%s' % (self.number, item['path']))
      requests_url =  item['path']
      if requests_url.startswith('/'):
        requests_url = "https://rsshub.mhuig.top" + requests_url + "?time=%s" % int(time.time())
        print("====== https://rsshub.mhuig.top ========> " + requests_url + " ======")
      else:
        print("====== " + requests_url + " ======")
      response = get_data(requests_url)
      if response.strip() == "" and item['path'].startswith('/'):
        requests_url = "https://rsshub.app" + item['path'] + "?time=%s" % int(time.time())
        print("====== https://rsshub.app ========> " + requests_url + " ======")
        response = get_data(requests_url)
      # time.sleep(random.randint(1, 3))
      self.data_list.put([response,item])  # 向数据队列里追加


def 解析文章():
  concurrent = 10
  conparse = 10

  # 生成请求队列
  req_list = queue.Queue()
  # 生成数据队列
  data_list = queue.Queue()

  # 填充请求数据
  for item in data:
    req_list.put(item)

  # 生成N个采集线程
  req_thread = []
  for i in range(concurrent):
    t = Crawl(i + 1, req_list, data_list)  # 创造线程
    t.start()
    req_thread.append(t)

  # 生成N个解析线程
  parse_thread = []
  for i in range(conparse):
    t = Parse(i + 1, data_list, req_thread)  # 创造解析线程
    t.start()
    parse_thread.append(t)

  for t in req_thread:
    t.join()
  for t in parse_thread:
    t.join()



route_config = load_config('config.route.yml')
path=[]
data=[]

print("--------- 解析路由配置文件 begin ---------")
dfs_route(route_config, path)
print("--------- 解析路由配置文件 end ---------")
print("--------- 解析文章 begin ---------")
解析文章()
print("--------- 解析文章 end ---------")