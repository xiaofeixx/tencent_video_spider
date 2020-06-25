# http://jx.du2.cc/?url=
# http://jx.drgxj.com/?url=
# http://jx.618ge.com/?url=
# http://vip.jlsprh.com/?url=
# http://jx.drgxj.com/?url=
# http://jx.598110.com/?url=
# http://jx.idc126.net/jx/?url=
import re, requests, json, time

file = open("text.txt", "w", encoding="utf-8")
body = requests.get(url="https://v.qq.com/x/cover/mzc00200gfkvdlo.html").content
body = str(body, "utf-8")
body = re.search("var COVER_INFO = ([\s\S]*)var COLUMN_INFO", body).group()
body = body.replace("var COVER_INFO = ", "")
body = body.replace("var COLUMN_INFO", "")
object = json.loads(body)
value = (
    object['title'],
    object['main_genre'],
    object['year'],
    object['vertical_pic_url'],
    object['new_pic_hz'],
    object['description'],
    object['director'],
    json.dumps(object['leading_actor']),
    object['publish_date'],
    object['current_num'],
    object['episode_all'],
    object['area_name'],
    # object['score']['score'],
    int(time.time()),
    object['payfree_num'],
    1,
    # object['score']['hot'],
    object['second_title'],
    object['langue']
)

key = ("title", 'title_en', 'main_genre', 'year', 'vertical_pic_url', 'new_pic_hz', 'description', 'pay_status',
       'leading_actor', 'publish_date', 'current_num', 'episode_all', 'area_name', 'payfree_num', 'second_title',
       'langue')
value = []
for k in key:
    if k in object:
        if isinstance(object[k], list):
            value.append(json.dumps(object[k]))
        elif isinstance(object[k], int):
            value.append(str(object[k]))
        else:
            value.append(object[k])
    else:
        value.append(str(0))
# value.append(str(object['score']['score']))
# value.append(str(object['score']['hot']))
value.append(str(1))
value.append(str(int(time.time())))
# value.append(object['director'])
print(value)
bb = tuple(value)
print(bb)
print(json.dumps(object['nomal_ids'][1]))