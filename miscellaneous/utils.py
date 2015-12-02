from django.template.defaultfilters import slugify

import json
import datetime
import requests

import miscellaneous.key
from miscellaneous.arrays import days, pairs

BotURL = "https://api.telegram.org/bot%s/" % miscellaneous.key.BOT_TOKEN


class StopExecution(Exception):
    pass


def reply(chat_id, msg=None, location=None, keyboard=None):
    if msg:
        reply_markup = {}
        if not keyboard:
            reply_markup['hide_keyboard'] = True
            requests.post(BotURL + 'sendMessage', data={
                'chat_id': str(chat_id),
                'text': msg.encode('utf-8'),
                'reply_markup': json.dumps(reply_markup),
            })
        else:
            reply_markup['keyboard'] = keyboard
            reply_markup['resize_keyboard'] = True
            reply_markup['one_time_keyboard'] = True

            requests.post(BotURL + 'sendMessage', data={
                'chat_id': str(chat_id),
                'text': msg.encode('utf-8'),
                'reply_markup': json.dumps(reply_markup),
            })
    elif location:
        requests.post(BotURL + 'sendLocation', data={
            'chat_id': str(chat_id),
            'latitude': location['latitude'],
            'longitude': location['longitude'],
        })


def get_group_id_by_name(group_name):
    from request_handler.models import Group
    try:
        # Check same groups (need specialization)
        query = Group.objects.all().filter(group_name__contains=group_name + "(")
        if len(query) != 0:
            return -2

        group = Group.objects.get(group_name=group_name)
        return group.group_id
    except Group.DoesNotExist:
        return -1


def get_group_name_by_id(group_id):
    from request_handler.models import Group
    if group_id == 0:
        return "Teacher"

    try:
        group = Group.objects.get(group_id=group_id)
        return group.group_name
    except Group.DoesNotExist:
        return False


def get_current_lesson_number():
    now = datetime.datetime.now()
    cur_lesson = 0
    for i in range(len(pairs) - 1):
        if now > pairs[i] and now < pairs[i + 1]:
            cur_lesson = i

    return cur_lesson


def is_cyrillic(s):
    return not len(slugify(s)) == len(s)


def transliterate(text):
    tr_en_ua = str.maketrans("abcdefghijklmnopqrstuvwxyz",
                             "абцдєфгхіжклмнопкрстуввхуз")
    if not is_cyrillic(text):
        return text.translate(tr_en_ua)
    return text


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