import json
import datetime
import requests

from django.template.defaultfilters import slugify
from django.http import HttpResponse
from django.conf import settings

from miscellaneous.arrays import days


class StopExecution(Exception):
    pass


def reply(chat_id, msg=None, location=None, keyboard=None, inline_keyboard=None):
    if msg:
        reply_markup = {}
        if not keyboard and not inline_keyboard:
            # ReplyKeyboardHide object
            reply_markup['hide_keyboard'] = True
        elif inline_keyboard:
            # InlineKeyboardMarkup object
            reply_markup['inline_keyboard'] = inline_keyboard
        else:
            # ReplyKeyboardMarkup object
            reply_markup['keyboard'] = keyboard
            reply_markup['resize_keyboard'] = True
            reply_markup['one_time_keyboard'] = True

        requests.post(settings.BOT_URL + 'sendMessage', data={
            'chat_id': str(chat_id),
            'text': msg.encode('utf-8'),
            'parse_mode': "Markdown",
            'reply_markup': json.dumps(reply_markup),
        })
    elif location:
        requests.post(settings.BOT_URL + 'sendLocation', data={
            'chat_id': str(chat_id),
            'latitude': location['latitude'],
            'longitude': location['longitude'],
        })


def update(chat_id, upd_message_id, text, inline_keyboard=False):
    reply_markup = {}
    if not inline_keyboard:
        # ReplyKeyboardHide object
        reply_markup['hide_keyboard'] = True
    elif inline_keyboard:
        # InlineKeyboardMarkup object
        reply_markup['inline_keyboard'] = inline_keyboard

    requests.post(settings.BOT_URL + 'editMessageText', data={
        'chat_id': str(chat_id),
        'message_id': upd_message_id,
        'text': text.encode('utf-8'),
        'parse_mode': "Markdown",
        'reply_markup': json.dumps(reply_markup),
    })


def get_group_id_by_name(group_name):
    from request_handler.models import Group
    try:
        # Check same groups (need specialization)
        query = Group.objects.filter(group_name__contains=group_name + "(")
        if query.exists():
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
        return None


def get_pairs():
    now = datetime.datetime.now()
    return [
        datetime.datetime(now.year, now.month, now.day, 0, 1),
        datetime.datetime(now.year, now.month, now.day, 8, 30),
        datetime.datetime(now.year, now.month, now.day, 10, 5),
        datetime.datetime(now.year, now.month, now.day, 12, 0),
        datetime.datetime(now.year, now.month, now.day, 13, 55),
        datetime.datetime(now.year, now.month, now.day, 15, 50),
        datetime.datetime(now.year, now.month, now.day, 17, 45),
        datetime.datetime(now.year, now.month, now.day, 23, 59)]


def get_current_lesson_number():
    now = datetime.datetime.now()
    pairs = get_pairs()
    for i in range(len(pairs) - 1):
        if now > pairs[i] and now < pairs[i + 1]:
            return i


def get_time_to_lesson_end(lesson_number):
    now = datetime.datetime.now()
    return str(int((get_pairs()[lesson_number + 1] - now).total_seconds() // 60))


def is_cyrillic(s):
    return not len(slugify(s)) == len(s)


def transliterate(text):
    tr_en_ua = str.maketrans("abcdefghijklmnopqrstuvwxyz",
                             "абцдефгхіжклмнопкрстуввхуз")
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
    return raw_data.json()['statusCode'] == 200


def prettify(timetable):
    """
    Reformat timetable dict:
    From: self.timetable[str(week)][str(day)][str(lesson_number)]
    To:   self.timetable[week][day][lesson_number]
    """
    result = {}
    for week in timetable:
        result[int(week)] = {}
        for day in timetable[week]:
            result[int(week)][int(day)] = {}
            for lesson in timetable[week][day]:
                result[int(week)][int(day)][int(lesson)] = timetable[week][day][lesson]
    return result


def get_current_week():
    return 2 - datetime.date.today().isocalendar()[1] % 2


def generate_rooms_string(rooms, responses):
    """
    Generate string like "339-19, 302-18" from rooms array
    """
    if not rooms:
        return responses['unknown_room'] + "\n"

    result = []
    for room in rooms:
        result.append("%s-%s" % (room['name'], room['building']['name']))

    return ', '.join(result) + "\n"

def send_log(func):
    def wrapper(request, *args, **kwargs):
        try:
            func(request)
        except:
            import traceback
            reply(settings.LOG_CHAT_ID, msg=traceback.format_exc())
            reply(settings.LOG_CHAT_ID, msg=request.body.decode())
        finally:
            return HttpResponse()
    return wrapper
