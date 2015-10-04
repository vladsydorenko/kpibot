import re
import datetime
import requests
import miscellaneous.key

from transliterate import translit
from django.template.defaultfilters import slugify
from miscellaneous.arrays import commands, days, time, pairs

BotURL = "https://api.telegram.org/bot%s/" % miscellaneous.key.BOT_TOKEN

class StopException(Exception):
    pass

def reply(chat_id, msg = None, location = None):
    if msg:
        requests.post(BotURL + 'sendMessage', data = {
            'chat_id': str(chat_id),
            'text': msg.encode('utf-8'),
        })
    elif location:
        requests.post(BotURL + 'sendLocation', data = {
            'chat_id': str(chat_id),
            'latitude' : location['latitude'],
            'longitude' : location['longitude'],
        })
    
def get_group_id_by_name(group_name):
    #TODO: Change in new API
    if '(' in group_name:
        group_name = group_name.split("(")[0] + " (" + group_name.split("(")[1]
        
    raw_data = requests.get("http://api.rozklad.org.ua/v2/groups/%s" % group_name)
    data = raw_data.json()
    if data['statusCode'] == 200:
        return data['data']['group_id']

    return False

def get_group_by_id(group_id):
    raw_data = requests.get("http://api.rozklad.org.ua/v2/groups/%s" % group_id)
    data = raw_data.json()
    if data['statusCode'] == 200:
        if group_id == 0:
            return "Teacher"
        else:
            return data['data']['group_full_name']

    return False

def get_current_lesson_number():    
    now = datetime.datetime.now()
    cur_lesson = 0;
    for i in range(len(pairs) - 1):
        if now > pairs[i] and now < pairs[i+1]:
            cur_lesson = i
            
    return cur_lesson

def translit_ru_en(group):
    if is_cyrillic(group):
        return translit(group, 'ru', reversed = True)
    else:
        return group

def is_cyrillic(s):
    return not len(slugify(s)) == len(s)

def get_week_day(token):
    for day in days:
        if token in days[day]:
            return day
    return False
        
def is_group_exists(group_id):
    raw_data = requests.get("http://api.rozklad.org.ua/v2/groups/%s" % group_id)
    if raw_data.json()['statusCode'] == 200:
        return True

    return False