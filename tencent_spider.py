import requests
from queue import Queue
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, wait
from threading import Thread, Lock
import threading
from requests.adapters import HTTPAdapter
import xlwt

start_queue = Queue(maxsize=-1)
h_queue = Queue(maxsize=-1)
lock = Lock()
headers = {
    'Accept': '',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/83.0.4103.97 Safari/537.36 ',
    'Connection': 'keep-alive',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
}

s = requests.Session()
s.mount('http://', HTTPAdapter(max_retries=3))
s.mount('https://', HTTPAdapter(max_retries=3))
workbook = xlwt.Workbook(encoding='utf-8', style_compression=0)
film_sheet = workbook.add_sheet("film", cell_overwrite_ok=True)
film_sheet_type = workbook.add_sheet('类型', cell_overwrite_ok=True)
film_sheet_count = 1
film_type_count = 1


def create_table_header():
    global film_sheet,film_sheet_type
    print("执行了")
    film_sheet.write(0, 0, 'id')
    film_sheet.write(0, 1, 'videoName')
    film_sheet.write(0, 2, 'director')
    film_sheet.write(0, 3, 'performer')
    film_sheet.write(0, 4, 'region')
    film_sheet.write(0, 5, 'play_url')
    film_sheet.write(0, 6, 'imgUrl')
    film_sheet.write(0, 7, 'introduction')
    film_sheet.write(0, 8, 'yearG')
    film_sheet.write(0, 9, 'score')
    film_sheet_type.write(0, 1, 'id')
    film_sheet_type.write(0, 2, 'type')


class url_object:
    def __init__(self, url, img_url):
        self.url = url
        self.img_url = img_url


# 解析文档
def parse_html(url):
    global headers, s
    try:
        response = s.get(url=url, headers=headers, timeout=5)
    except requests.exceptions.RequestException as e:
        return False
    response.encoding = 'utf-8'
    parse_result = BeautifulSoup(response.text, 'lxml')
    return parse_result


def construct_start_queue():
    for i in range(0, 4980, 30):
        start_queue.put(
            "https://v.qq.com/x/bu/pagesheet/list?_all=1&append=1&channel=movie&listpage=2&offset=%s&pagesize=30&sort"
            "=18" % i)


executor = ThreadPoolExecutor(max_workers=8)


def parse_list():
    global start_queue, h_queue, film_sheet_count
    while True:
        if start_queue.empty():
            print("当前线程%s解析完毕" % threading.current_thread().getName())
            break
        list_url = start_queue.get()
        start_queue.task_done()
        result = parse_html(list_url)
        if not result:
            print("放弃解析%s" % list_url)
            continue
        film_items = result.find_all(attrs={'class': 'figure'})
        for i in film_items:
            print(i['href'])
            print("http://%s" % i.img['src'])
            h_queue.put(url_object(i['href'], 'http://%s' % i.img['src']))


def parse_and_store(detail_result, detail_page):
    x_flag = 1
    y_flag = 1
    global film_type_count, film_sheet_count, film_sheet, film_sheet_type,lock
    performer = ''
    for i in detail_result.find_all(attrs={'class': 'video_tags _video_tags'}):
        sub_category = i.find_all(attrs={'class': 'tag_item'})
        for x in sub_category:
            if x_flag == 1:
                t = x.text.replace(' ', '')
                sm = t.replace('\n', '')
                if sm == '豆豆瓣高分':
                    continue
                else:
                    film_sheet.write(film_sheet_count, 4, x.text)
                    print('地区:%s' % x.text)
            elif x_flag == 2:
                film_sheet.write(film_sheet_count, 8, x.text)
                print("年份%s" % x.text)
            else:
                film_sheet_type.write(film_type_count, 0, film_sheet_count)
                film_sheet_type.write(film_type_count, 1, x.text)
                with lock:
                    film_type_count += 1
            x_flag += 1
    for m in detail_result.find(attrs={'class': 'director'}).find_all('a'):
        if y_flag == 1:
            film_sheet.write(film_sheet_count, 2, m.text)
            print("导演:%s" % m.text)
            y_flag += 1
            continue
        performer += m.text
        y_flag += 1
    print('演员%s' % performer)
    film_sheet.write(film_sheet_count, 3, performer)
    print(detail_result.find(attrs={'class': 'summary'}).text)
    film_sheet.write(film_sheet_count, 7, detail_result.find(attrs={'class': 'summary'}).text)
    print(detail_result.find(attrs={'class': 'player_title'}).text)
    film_sheet.write(film_sheet_count, 1, detail_result.find(attrs={'class': 'player_title'}).text)
    print(detail_page.img_url)
    film_sheet.write(film_sheet_count, 6, detail_page.img_url)
    print(detail_page.url)
    film_sheet.write(film_sheet_count, 5, detail_page.url)
    try:
        print(""+detail_result.find(attrs={'class': 'video_score'}).find(attrs={'class': 'units'}).text + detail_result.find(
            attrs={'class': 'video_score'}).find(attrs={'class': 'decimal'}).text)
        film_sheet.write(film_sheet_count, 9, detail_result.find(attrs={'class': 'video_score'}).find(
            attrs={'class': 'units'}).text + detail_result.find(
            attrs={'class': 'video_score'}).find(attrs={'class': 'decimal'}).text)
    except AttributeError as e:
        print("评分不存在%s" % e)
    film_sheet_count += 1


def parse_detail():
    global h_queue
    while True:
        if h_queue.empty():
            print("当前细节线程%s解析完毕" % threading.current_thread().getName())
            break
        detail_page = h_queue.get()
        h_queue.task_done()
        detail_result = parse_html(detail_page.url)
        if not detail_result:
            print('放弃解析%s' % detail_page)
            continue
        with lock:
            parse_and_store(detail_result, detail_page)


task_list = []
construct_start_queue()
for i in range(0, 9):
    task = executor.submit(parse_list)
    task_list.append(task)

start_queue.join()
print(wait(task_list))

print("====列表页解析完毕====")
task_list2 = []

# for i in range(0, 9):
#     task = executor.submit(parse_detail)
#     task_list2.append(task)

h_queue.join()
wait(task_list2)
print("=====详情页解析完毕======")
print(film_sheet_count)
workbook.save('电影表格.xls')
