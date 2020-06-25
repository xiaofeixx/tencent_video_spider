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
wordbook = xlsxwriter.Workbook('动漫数据.xlsx')
tv_letter = wordbook.add_worksheet('电视剧信息')
tv_type = wordbook.add_worksheet('电视类型')
tv_episodes = wordbook.add_worksheet('电视集数')
tv_letter_count = 1
tv_type_count = 1
tv_episodes_count = 1
lock = Lock()


def create_table_header():
    global film_sheet, film_sheet_type
    print("执行了")
    tv_letter.write(0, 0, 'id')
    tv_letter.write(0, 1, 'videoName')
    tv_letter.write(0, 2, 'director')
    tv_letter.write(0, 3, 'performer')
    tv_letter.write(0, 4, 'region')
    tv_letter.write(0, 5, 'publish_time')
    tv_letter.write(0, 6, 'imgUrl')
    tv_letter.write(0, 7, 'introduction')
    tv_letter.write(0, 8, 'yearG')
    tv_letter.write(0, 9, 'score')
    tv_type.write(0, 0, 'tv_id')
    tv_type.write(0, 1, 'type')
    tv_episodes.write(0, 0, 'episodes_num')
    tv_episodes.write(0, 1, 'tv_id')
    tv_episodes.write(0, 2, 'episodes_url')
    tv_episodes.write(0, 3, 'vip')


def construct_tv_queue():
    for i in range(0, 1860, 30):
        tv_queue.put(
            "https://v.qq.com/x/bu/pagesheet/list?_all=1&append=1&channel=cartoon&listpage=2&offset=%s&pagesize=30&sort"
            "=18" % i)


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
    while True:
        if tv_queue.empty():
            print("当前线程%s解析完毕" % threading.current_thread().getName())
            break
        list_url = tv_queue.get()
        tv_queue.task_done()
        result = parse_html(list_url)
        if not result:
            print("放弃解析%s" % list_url)
            continue
        film_items = result.find_all(attrs={'class': 'figure'})
        for i in film_items:
            print(i['href'])
            print("http://%s" % i.img['src'])
            tv_list_queue.put(url_object(i['href'], 'http://%s' % i.img['src']))


def parse_result():
    global tv_list_queue, tv_type, tv_letter, tv_episodes
    global tv_type_count, tv_letter_count, tv_episodes_count
    while True:
        if tv_list_queue.empty():
            print("当前%s线程解析完毕" % threading.current_thread().getName())
            break
        url_obj = tv_list_queue.get()
        tv_list_queue.task_done()
        object_result = parse_html_object(url_obj.url)
        if not object_result:
            print("当前线程%s放弃解析%s" % (threading.current_thread().getName(), url_obj.url))
            continue
        if object_result['pay_status'] == 6:
            member = 1
        else:
            member = 0
        if 'title_en' in object_result:
            en = object_result['title_en']
        else:
            en = "none"
        print(object_result['title'])
        print(object_result['director'])
        director = ''
        if object_result['director']:
            for i in object_result['director']:
                director += i + ','
        print(object_result['leading_actor'])
        performer = ''
        if object_result['leading_actor']:
            for i in object_result['leading_actor']:
                performer += i + ','
        with lock:
            tv_letter.write(tv_letter_count, 2, director.rstrip(','))
            tv_letter.write(tv_letter_count, 0, tv_letter_count)
            tv_letter.write(tv_letter_count, 1, object_result['title'])
            tv_letter.write(tv_letter_count, 3, performer.rstrip(','))
            print(object_result['area_name'])
            tv_letter.write(tv_letter_count, 4, object_result['area_name'])
            print(url_obj.img_url)
            tv_letter.write(tv_letter_count, 6, url_obj.img_url)
            print(object_result['description'])
            tv_letter.write(tv_letter_count, 7, object_result['description'])
            print(object_result['year'])
            tv_letter.write(tv_letter_count, 8, object_result['year'])
            print(object_result['publish_date'])
            tv_letter.write(tv_letter_count, 5, object_result['publish_date'])
            print(object_result['score']['score'])
            tv_letter.write(tv_letter_count, 9, object_result['score']['score'])
            print(object_result['nomal_ids'])
            url_prefix = url_obj.url.replace('.html', '')
            if object_result['nomal_ids']:
                for i in object_result['nomal_ids']:
                    tv_episodes.write(tv_episodes_count, 0, i['E'])
                    tv_episodes.write(tv_episodes_count, 1, tv_letter_count)
                    tv_episodes.write(tv_episodes_count, 2, '%s/%s.html' % (url_prefix, i['V']))
                    tv_episodes.write(tv_episodes_count, 3, i['F'])
                    tv_episodes_count += 1
                    print('集数%s' % tv_episodes_count)
            print(object_result['subtype'])
            if object_result['subtype']:
                for i in object_result['subtype']:
                    tv_type.write(tv_type_count, 0, tv_letter_count)
                    print(i)
                    tv_type.write(tv_type_count, 1, i)
                    tv_type_count += 1
                    print('类型%s' % tv_type_count)
            tv_letter_count += 1
            print(tv_letter_count)


create_table_header()
construct_tv_queue()

list_task = []
for i in range(1, 9):
    task = executor.submit(parse_tv_list)
    list_task.append(task)
tv_queue.join()
print(wait(list_task))
print('=================列表页解析完毕=====================')
parse_tv_list()
tv_queue.join()

result_task = []

for i in range(0, 8):
    task = executor.submit(parse_result)
    result_task.append(task)

tv_list_queue.join()
print(wait(result_task))
print('==========电视剧解析完毕============')
print('=======写入完毕======')
wordbook.close()

# id = 5010