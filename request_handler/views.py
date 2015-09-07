# -*- coding: UTF-8 -*-
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.template.defaultfilters import slugify 
from request_handler.models import Chat
from transliterate import translit
from django.http import HttpResponse
from PIL import Image
import re
import os
import io
import time
import json
import logging
import requests
from miscellaneous.multipart import post_multipart
import datetime
import traceback
#Support different languages (ru, ua)
import miscellaneous.lang

#Dictionary for answers
on = None

days = {1: ["mon", "pn"],
        2: ["tue", "vt"],
        3: ["wed", "sr"],
        4: ["thu", "cht"],
        5: ["fri", "pt"],
        6: ["sat", "sb"],
        7: ["sun", "vs"]}

#Place for your bot token
BOT_TOKEN = ""
BotURL = "https://api.telegram.org/bot%s/" % BOT_TOKEN

log = logging.getLogger("request_handler")

def get_current_lesson_number():
    #Set timezone
    os.environ['TZ'] = 'Europe/Kiev'
    time.tzset()
    
    now = datetime.datetime.now()
    #Timetable
    pairs = [
        datetime.datetime(now.year, now.month, now.day, 8, 30),
        datetime.datetime(now.year, now.month, now.day, 10, 5),
        datetime.datetime(now.year, now.month, now.day, 12, 00),
        datetime.datetime(now.year, now.month, now.day, 13, 55),
        datetime.datetime(now.year, now.month, now.day, 15, 50),
        datetime.datetime(now.year, now.month, now.day, 17, 45),
        datetime.datetime(now.year, now.month, now.day, 23, 59)]
        
    cur_pair = 0;
    for i in range(len(pairs) - 1):
        if now > pairs[i] and now < pairs[i+1]:
            cur_pair = i + 1
            
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

def reply(chat_id, msg = None, img = None):
    try:
        if msg:
            requests.post(BotURL + 'sendMessage', data = {
                'chat_id': str(chat_id),
                'text': msg.encode('utf-8'),
            })
        elif img:
            multipart.post_multipart(BotURL + 'sendPhoto', 
            [('chat_id', str(chat_id))],
            [('photo', 'image.jpg', img)])
        else:
            log.error("no msg or img specified")
    except Exception:
       log.error(traceback.format_exc())

def is_group_exists(group):
    raw_data = requests.get("http://api.rozklad.org.ua/v2/groups/%s" % group)
    if raw_data.json()['statusCode'] == 200:
        return True
    else:
        return False
        
def set_group(chat_id, group):
    if is_group_exists(group):
        c = Chat(chat_id = chat_id, group = group)
        c.save()
        reply(chat_id, msg = on['setgroup_success'])
    else:
        reply(chat_id, msg = on['setgroup_fail'])
        
def get_one_pair(chat_id, group,\
                 next = False, teacher = False,\
                 cur_lesson = -1, week_day = -1,\
                 change_week_number = False):
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

        if not change_week_number:
            week_number = datetime.date.today().isocalendar()[1] % 2 + 1
        else:
            week_number = 3 - (datetime.date.today().isocalendar()[1] % 2 + 1)

        filter = "{" + "\'day_number\':{0},\'lesson_week\':{1}".format(week_day, week_number) + "}"
        log.info(filter)
        raw_data = requests.get("http://api.rozklad.org.ua/v2/groups/{0}/lessons?filter={1}".format(group, filter))
        data = raw_data.json()

        if data['statusCode'] == 200:
            i = 0
            while i < len(data['data']) and int(data['data'][i]['lesson_number']) < cur_lesson:
                i += 1

            if i == len(data['data']):
                if week_day == 7:
                    get_one_pair(chat_id, group, cur_lesson = 1, week_day = 1, change_week_number = True)
                else:
                    get_one_pair(chat_id, group, cur_lesson = 1, week_day = week_day + 1)
                return
                
            if teacher:
                reply(chat_id, msg = data['data'][i]['teachers'][0]['teacher_full_name'])
            else:
                lesson = on['week_days'][week_day] + ":\n"
                lesson += data['data'][i]['lesson_number'] + ": " + data['data'][i]['lesson_name'] + " - " + \
                (data['data'][i]['lesson_room'] if data['data'][i]['lesson_room']
                                                else on['unknown_room'])
                reply(chat_id, msg = lesson)
               
        else:
            if not next:
                reply(chat_id, msg = on['get_tt_error'])
            else:
                if week_day == 7:
                    get_one_pair(chat_id, group, cur_lesson = 1, week_day = 1, change_week_number = True)
                else:
                    log.info("+1")
                    get_one_pair(chat_id, group, cur_lesson = 1, week_day = week_day + 1)
    except Exception:
            log.error(traceback.format_exc())
        
def get_day_timetable(chat_id, group, week_day_param, week_num_param,
                      show_teacher = False, tomorrow = False,\
                      full_lesson_name = False, full_timetable = False):
    try:
        if not group:
            reply(chat_id, msg = on['empty_group'])
            return

        week_day = datetime.date.today().weekday() + 1

        if week_day_param != 0:
            week_day = week_day_param

        if tomorrow:
            if week_day == 7:
                week_day = 1
            else:
                week_day += 1
        else:
            if week_day == 7:
                reply(chat_id, msg = on['sunday'])
                return

        if week_num_param == 0:
            week_number = datetime.date.today().isocalendar()[1] % 2 + 1
        else:
            week_number = week_num_param
 
        filter = "{" + "\'day_number\':{0},\'lesson_week\':{1}".format(week_day, week_number) + "}"
        raw_data = requests.get("http://api.rozklad.org.ua/v2/groups/{0}/lessons?filter={1}".format(group, filter))
        data = raw_data.json()
        if data['statusCode'] == 200:
            timetable = on['week_days'][week_day] + ":\n"
            for lesson in data['data']:
                timetable += lesson['lesson_number'] + ": " + \
                (lesson['lesson_full_name'] if full_lesson_name else lesson['lesson_name']) + " - " + \
                (lesson['lesson_room'] if lesson['lesson_room'] else on['unknown_room']) + "\n"
                if show_teacher:
                    timetable += "--- " + lesson['teachers'][0]['teacher_full_name'] + "\n"

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
        chat = Chat.objects.get(pk = chat_id)
    #Unknown request
    except KeyError:
        log.error(traceback.format_exc())
        return HttpResponse()
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
        on = miscellaneous.lang.ru
    else:
        on = miscellaneous.lang.ua

    group = chat.group #Default ""
    week_number = 0
    week_day = 0
    log.info(message)
    #Process parameters
    if len(message.split()) > 1:
        for token in message.split():
            token = translit_ru_en(token)
            if re.match("[A-z][A-z][-][[0-9][0-9]", token):
                group = token
            elif re.match("[w][1|2]", token):
                week_number = int(token[1])
            elif re.match("[w][3-9]", token):
                reply(chat_id, msg = on['wrong_week_param'])
                return HttpResponse()
            elif re.match("[1-7]", token):
                week_day = int(token)
            elif is_week_day(token) != 0:
                week_day = is_week_day(token)
            elif re.match("\w", token):
                reply(chat_id, msg = on['wrong_param'])
                return HttpResponse()
            
        if not group and week_number == 0 and week_day == 0:
            reply(chat_id, msg = on['wrong_param'])
            return HttpResponse()
       
    #Command processing  
    try:    
        if message == '/start' or message.startswith("/help"):
            reply(chat_id, msg = on['help'])

        elif message == '/pig':
            output = io.StringIO()
            img = Image.open("./request_handler/poreju.jpg")
            img.save(output, 'JPEG')
            reply(chat_id, img = output.getvalue())
            
        elif message.startswith('/setgroup'):
            if len(message.split()) == 1:
                reply(chat_id, msg = on['setgroup_empty_param'])
            else:
                set_group(chat_id, group)
            
        #TODO For debug. Delete on release    
        elif message == '/getall':
            all_chats = Chat.objects.all()
            for chat in all_chats:
                reply(chat_id, msg = chat.chat_id + " - " + chat.group)
                
        elif message == '/changelang':
            if chat.language == "ru":
                chat.language = "ua"
                reply(chat_id, msg = miscellaneous.lang.ua['change_lang'])
            else:
                chat.language = "ru"
                reply(chat_id, msg = miscellaneous.lang.ru['change_lang'])
            chat.save()

        elif message.startswith("/tt"):
            if week_number == 0:
                week_range = list(range(1,3))
            else:
                week_range = [week_number]
            for week_num in week_range:
                if week_day == 0:
                    reply(chat_id, msg = "Week #" + str(week_num))
                    for week_day_iter in list(range(1,7)):
                        get_day_timetable(chat_id, group,\
                                          week_day_param = week_day_iter,\
                                          week_num_param = week_num,\
                                          full_timetable = True)
                else:
                    get_day_timetable(chat_id, group,\
                                          week_day_param = week_day,\
                                          week_num_param = week_num)
        
        #Hidden function
        elif message.startswith("/ttfullname"):
            get_day_timetable(chat_id, group, week_day, week_number, full_lesson_name = True)
            
        elif message.startswith('/today'):
            get_day_timetable(chat_id, group, week_day, week_number)
                
        elif message.startswith("/teacher"):
            get_day_timetable(chat_id, group, week_day, week_number, show_teacher = True)
            
        elif message.startswith("/tomorrow"): 
            get_day_timetable(chat_id, group, week_day, week_number, tomorrow = True)

        elif message.startswith("/now"):
            get_one_pair(chat_id, group)
        
        elif message == "/authors":
            reply(chat_id, msg = on['authors'])
            
        elif message == "/next":
            get_one_pair(chat_id, group, next = True)  
        
        elif message == "/who":
            get_one_pair(chat_id, group, teacher = True)   
        
        
    except Exception:
        log.error(traceback.format_exc())
    return HttpResponse()

def lalka(request):
    mamka = 5
    mamka += 'ahaha'
    return HttpResponse(('hoho', 'lala'))
