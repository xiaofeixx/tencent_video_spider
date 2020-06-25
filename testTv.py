import re, json, requests, threading, xlsxwriter
from queue import Queue
from threading import Lock
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, wait
from requests.adapters import HTTPAdapter

tv_queue = Queue(maxsize=-1)
tv_list_queue = Queue(maxsize=-1)
s = requests.Session()
s.mount('http://', HTTPAdapter(max_retries=3))
s.mount('https://', HTTPAdapter(max_retries=3))
headers = {
    'Accept': '',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/83.0.4103.97 Safari/537.36 ',
    'Connection': 'keep-alive',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
}
lock = Lock()


class url_object:
    def __init__(self, url, img_url):
        self.url = url
        self.img_url = img_url


def parse_html(url):
    global headers, s
    try:
        response = s.get(url=url, headers=headers, timeout=5)
    except requests.exceptions.RequestException as e:
        return False
    response.encoding = 'utf-8'
    parse_result = BeautifulSoup(response.text, 'lxml')
    return parse_result


# 解析文档
def parse_html_object(url):
    global headers, s
    try:
        response = s.get(url=url, headers=headers, timeout=5).content
    except requests.exceptions.RequestException as e:
        return False
    response = str(response, 'utf-8')
    response = re.search("var COVER_INFO = ([\s\S]*)var COLUMN_INFO", response).group()
    response = response.replace("var COVER_INFO = ", "")
    response = response.replace("var COLUMN_INFO", "")
    object_result = json.loads(response)
    return object_result


executor = ThreadPoolExecutor(max_workers=8)


def parse_tv_list():
    global tv_queue
    tv_list_queue.put('https://v.qq.com/x/cover/mzc00200rn5n6ho/x0980tgt90f.html',
                      'https://v.qq.com/x/cover/mzc00200rn5n6ho/x0980tgt90f.html')


tv_list_queue.put(url_object('https://v.qq.com/x/cover/mzc00200rn5n6ho/x0980tgt90f.html','https://v.qq.com/x/cover/mzc00200rn5n6ho/x0980tgt90f.html'))


def parse_result():
    if tv_list_queue.empty():
        print("当前%s线程解析完毕" % threading.current_thread().getName())
    url_obj = tv_list_queue.get()
    tv_list_queue.task_done()
    object_result = parse_html_object(url_obj.url)
    if not object_result:
        print("当前线程%s放弃解析%s" % (threading.current_thread().getName(), url_obj.url))
    print(object_result['title'])
    print(object_result['director'])
    director = ''
    if object_result['director'] and len(object_result['director'] > 0):
        for i in object_result['director']:
            director += i + ','
    print(object_result['leading_actor'])
    performer = ''
    if object_result['leading_actor'] and len(object_result['leading_actor'] > 0):
        for i in object_result['leading_actor']:
            performer += i + ','
    with lock:
        print(object_result['area_name'])
        print(url_obj.img_url)
        print(object_result['description'])
        print(object_result['year'])
        print(object_result['publish_date'])
        print(object_result['score']['score'])
        print(object_result['nomal_ids'])
        url_prefix = url_obj.url.replace('.html', '')
        if object_result['nomal_ids']:
            for i in object_result['nomal_ids']:
                print(i)
        print(object_result['subtype'])
        if object_result['subtype'] and len(object_result['subtype']) > 0:
            for i in object_result['subtype']:
                print(i)

parse_result()