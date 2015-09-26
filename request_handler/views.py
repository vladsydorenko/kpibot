#!/usr/bin/python
# -*- coding: UTF-8 -*-
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.template.defaultfilters import slugify
from request_handler.models import Chat
from django.http import HttpResponse
from django.core.mail import mail_admins
from transliterate import translit

import re
import os
import io
import time
import json
import logging
import requests
import datetime
import traceback
import miscellaneous.key
#Support different languages (ru, ua)
from miscellaneous.lang   import ru, ua
from miscellaneous.botan  import track
from miscellaneous.arrays import commands, days, time, pairs

#Dictionary for answers
on = None

BotURL = "https://api.telegram.org/bot%s/" % miscellaneous.key.BOT_TOKEN

log = logging.getLogger("request_handler")

def get_current_lesson_number():    
    now = datetime.datetime.now()
    cur_pair = 0;
    for i in range(len(pairs) - 1):
        if now > pairs[i] and now < pairs[i+1]:
            cur_pair = i
            
    return cur_pair

def is_cyrillic(s):
    return not len(slugify(s)) == len(s)

def is_week_day(token):
    try:
        for day in days:
            if token in days[day]:
                return day
        return 0
    except Exception:
        log.error(traceback.format_exc())
    
def translit_ru_en(group):
    if is_cyrillic(group):
        return translit(group, 'ru', reversed = True)
    else:
        return group

def reply(chat_id, msg = None, location = None):
    try:
        if msg:
            requests.post(BotURL + 'sendMessage', data = {
                'chat_id': str(chat_id),
                'text': msg.encode('utf-8'),
            })
        elif location:
            log.info(location)
            requests.post(BotURL + 'sendLocation', data = {
                'chat_id': str(chat_id),
                'latitude' : location['latitude'],
                'longitude' : location['longitude'],
            })
    except Exception:
       log.error(traceback.format_exc())

def is_group_exists(group):
    raw_data = requests.get("http://api.rozklad.org.ua/v2/groups/%s" % group)
    if raw_data.json()['statusCode'] == 200:
        return True
    else:
        return False
        
def set_group(chat_id, group):
    c = Chat(chat_id = chat_id, group = group)
    c.save()
    reply(chat_id, msg = on['setgroup_success'])
        
def get_one_pair(chat_id, group, show_teacher = False,\
                 next = False, cur_lesson = -1,\
                 week_day = -1, week_number = 0,\
                 show_time_to_end = False, location = False):
    try:
        if not group:
            reply(chat_id, msg = on['empty_group'])
            return

        if week_day == -1:
            week_day = datetime.date.today().weekday() + 1

        if cur_lesson == -1:
            cur_lesson = get_current_lesson_number()
        elif cur_lesson == 6:
            week_day  += 1
            cur_lesson = 1

        if next:
            cur_lesson += 1

        if cur_lesson == 0:
            reply(chat_id, msg = on['no_lesson'])
            return

        if week_number == 0:
            week_number = datetime.date.today().isocalendar()[1] % 2 + 1

        filter = "{" + "\'day_number\':{0},\'lesson_week\':{1}".format(week_day, week_number) + "}"
        raw_data = requests.get("http://api.rozklad.org.ua/v2/groups/{0}/lessons?filter={1}".format(group, filter))
        data = raw_data.json()
        if data['statusCode'] == 200:
            i = 0
            while i < len(data['data']) and int(data['data'][i]['lesson_number']) < cur_lesson:
                i += 1

            if i == len(data['data']):
                if not next:
                    reply(chat_id, msg = on['no_lesson'])
                    return

                if week_day == 7:
                    get_one_pair(chat_id, group, cur_lesson = 1, week_day = 1, week_number = 3 - week_number, next = next)
                else:
                    get_one_pair(chat_id, group, cur_lesson = 1, week_day = week_day + 1, next = next)
                return

            # /where command
            if location:
                coordinates = {}
                coordinates['longitude'] = float(data['data'][i]['rooms'][0]['room_longitude'])
                coordinates['latitude'] = float(data['data'][i]['rooms'][0]['room_latitude'])
                reply(chat_id, location = coordinates)

            # Generating message body
            lesson = on['week_days'][week_day] + ":\n"
            lesson += data['data'][i]['lesson_number'] + ": " + data['data'][i]['lesson_name'] + " - " + \
            (data['data'][i]['lesson_room'] if data['data'][i]['lesson_room']
                                            else on['unknown_room']) + "\n"

            # t parameter
            if show_teacher:
                if len(data['data'][i]['teachers']) > 0:
                    for show_teacher in data['data'][i]['teachers']:
                        lesson += "--- " + show_teacher['teacher_full_name'] + "\n"
                else:
                    lesson += "--- " + on['no_teacher'] + "\n"

            # Add showing time to the end or lesson
            if show_time_to_end:
                now = datetime.datetime.now()
                time_to_end = str((pairs[get_current_lesson_number() + 1] - now).seconds // 60)
                reply(chat_id, msg = lesson + on['minutes_left'].format(time_to_end))
            else:
                reply(chat_id, msg = lesson)
        else:
            if not next:
                reply(chat_id, msg = on['get_tt_error'])
            else:
                if week_day == 7:
                    get_one_pair(chat_id, group, cur_lesson = 1, week_day = 1, week_number = 3 - week_number, next = next)
                else:
                    get_one_pair(chat_id, group, cur_lesson = 1, week_day = week_day + 1, next = next)
    except Exception:
            log.error(traceback.format_exc())

def get_day_timetable(chat_id, group, week_day, week_number,
                      show_teacher, tomorrow = False, full_timetable = False):
    try:
        if week_day == 0:
            week_day = datetime.date.today().weekday() + 1

        if tomorrow:
            if week_day == 7:
                week_day = 1
                week_number = 3 - week_number
            else:
                week_day += 1
        else:
            if week_day == 7:
                reply(chat_id, msg = on['sunday'])
                return

        if week_number == 0:
            week_number = datetime.date.today().isocalendar()[1] % 2 + 1

 
        filter = "{" + "\'day_number\':{0},\'lesson_week\':{1}".format(week_day, week_number) + "}"
        raw_data = requests.get("http://api.rozklad.org.ua/v2/groups/{0}/lessons?filter={1}".format(group, filter))
        data = raw_data.json()
        if data['statusCode'] == 200:
            timetable = on['week_days'][week_day] + ":\n"

            for lesson in data['data']:
                timetable += lesson['lesson_number'] + ": " + lesson['lesson_name'] + \
                (" (" + lesson['lesson_type'] + ")" if lesson['lesson_type'] else "") + " - " + \
                (lesson['lesson_room'] if lesson['lesson_room'] else on['unknown_room']) + "\n"

                if show_teacher:
                    if len(lesson['teachers']) > 0:
                        for teacher in lesson['teachers']:
                            timetable += "--- " + teacher['teacher_full_name'] + "\n"
                    else:
                        timetable += "--- " + on['no_teacher'] + "\n"

            reply(chat_id, msg = timetable)
        else:
            if not full_timetable:
                reply(chat_id, msg = on['get_tt_error'])
            else:
                return False
    except Exception:
            log.error(traceback.format_exc())
    
@csrf_exempt
@require_http_methods(["POST"])
def index(request):
    chat = Chat()
    message = ""
    chat_id = ""
    try:        
        data = json.loads(request.body.decode('utf-8'))
        chat_id = data['message']['chat']['id']
        message = data['message']['text']
        user_id = data['message']['from']['id']
        chat = Chat.objects.get(pk = chat_id)
    #If chat not in database
    except Chat.DoesNotExist:
        chat = Chat(chat_id = chat_id, group = "")
        chat.save()
    except Exception:
        log.error(traceback.format_exc())
        return HttpResponse()

    #Set user language
    global on
    if chat.language == "ru":
        on = ru
    else:
        on = ua

    if message.startswith("/bug") or message.startswith("/idea"):
        mail_admins('Bug or Idea', message)
        reply(chat_id, msg = on['email_sent'])
        return HttpResponse()        

    group = chat.group #Default ""
    week_number = 0
    week_day = 0
    lesson_number = 0
    show_teacher = False
    log.info(message)
    
    if message.split()[0].split('@')[0] not in commands:
        return HttpResponse()

    #Process parameters
    try:
        if len(message.split()) > 1:
            for token in message.split():
                #TODO Костыли и велосипеды
                if not u"ц" in token and not "(" in token:
                    token = translit_ru_en(token)
                else:
                    group = token
                    continue

                if re.match("[A-z][A-z][-][A-z]?[0-9][0-9][A-z]?([(]\w+[)])?", token):
                    group = token
                elif re.match("[A-z][A-z][A-z]?[0-9][0-9][A-z]?([(]\w+[)])?", token):
                    group = token[:2] + '-' + token[2:]
                elif re.match("[w][1|2]", token):
                    week_number = int(token[1])
                elif re.match("[w][3-9]", token):
                    reply(chat_id, msg = on['wrong_week_param'])
                    return HttpResponse()
                elif re.match("[1-6]", token):
                    lesson_number = int(token)
                elif re.match("[t|T]", token):
                    show_teacher = True
                elif is_week_day(token) != 0:
                    week_day = is_week_day(token)
                elif token not in commands:
                    reply(chat_id, msg = on['wrong_param'])
                    return HttpResponse()
                
            if not group and week_number == 0 and week_day == 0 and lesson_number == 0:
                reply(chat_id, msg = on['wrong_param'])
                return HttpResponse()

            #For groups like mv-31(r)
            if len(group.split("(")) > 1:
                group = group.split("(")[0] + " (" + group.split("(")[1]

    except Exception:
        log.error(traceback.format_exc())

    # Check group correctness and existance
    if group and not is_group_exists(group):
        reply(chat_id, msg = on['setgroup_fail'])
        return HttpResponse()
    elif not group:
        reply(chat_id, msg = on['empty_group'])
        return

    # Check wrong parameters
    if (week_day != 0 or week_number != 0 or lesson_number != 0) and (not message.startswith("/tt")):
        reply(chat_id, msg = on['now_parameters'].format(message.split()[0].split('@')[0]))
        return HttpResponse()

    # Statistics
    track(miscellaneous.key.BOTAN_TOKEN, user_id, {group : 1}, "Group") 
    track(miscellaneous.key.BOTAN_TOKEN, user_id, {}, message.split()[0].split('@')[0])

    #Command processing 
    try:    
        if message == '/start' or message.startswith("/help"):
            reply(chat_id, msg = on['help'])

        elif message.startswith('/setgroup'):
            if len(message.split()) == 1:
                reply(chat_id, msg = on['setgroup_empty_param'])
            else:
                set_group(chat_id, group)
                
        elif message == '/changelang':
            if chat.language == "ru":
                chat.language = "ua"
                reply(chat_id, msg = ua['change_lang'])
            else:
                chat.language = "ru"
                reply(chat_id, msg = ru['change_lang'])
            chat.save()

        elif message.startswith("/tt"):
            #To specify lesson number
            if lesson_number != 0:
                if week_day != 0 and week_number != 0:
                    get_one_pair(chat_id, group, show_teacher=show_teacher, cur_lesson=lesson_number)
                else:
                    reply(chat_id, msg = on['should_specify_params'])
                return HttpResponse()

            if week_number == 0:
                week_range = list(range(1,3))
            else:
                week_range = [week_number]
            for week_num in week_range:
                reply(chat_id, msg = "Week #" + str(week_num) + ":")
                if week_day == 0:
                    for week_day_iter in list(range(1,7)):
                        get_day_timetable(chat_id, group,\
                                          week_day_iter,\
                                          week_num, show_teacher,\
                                          full_timetable = True)
                else:
                    get_day_timetable(chat_id, group,\
                                      week_day,\
                                      week_num, show_teacher)
        
        elif message.startswith('/today'):
            get_day_timetable(chat_id, group, week_day, week_number, show_teacher)
            
        elif message.startswith("/tomorrow"): 
            get_day_timetable(chat_id, group, week_day, week_number, show_teacher, tomorrow = True)

        elif message.startswith("/now"):
            get_one_pair(chat_id, group, show_teacher=show_teacher, show_time_to_end = True)

        elif message.startswith("/where"):
            get_one_pair(chat_id, group, location = True)
        
        elif message.startswith("/authors"):
            reply(chat_id, msg = on['authors'])
            
        elif message.startswith("/next"):
            get_one_pair(chat_id, group, show_teacher = show_teacher, next = True)  
        
        elif message.startswith("/who"):
            get_one_pair(chat_id, group, show_teacher = True)

        elif message.startswith("/week"):
            reply(chat_id, msg = on['week'].format(datetime.date.today().isocalendar()[1] % 2 + 1))

        elif message.startswith("/time"):
            reply(chat_id, msg = time)
        
    except Exception:
        log.error(traceback.format_exc())
    return HttpResponse()
