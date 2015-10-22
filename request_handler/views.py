# -*- coding: UTF-8 -*-
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from request_handler.models import Chat
from django.http import HttpResponse
from django.core.mail import mail_admins

import json
import logging
import traceback
import datetime
#Support different languages (ru, ua)
from miscellaneous.lang   import ru, ua
from miscellaneous.botan  import track
from miscellaneous.arrays import commands, no_timetable_commands, time
from miscellaneous.utils import reply, get_group_name_by_id
from request_handler.timetable import GroupTimetable, TeacherTimetable
import miscellaneous.key

@csrf_exempt
@require_http_methods(["POST"])
def index(request):
    chat = Chat()
    message = ""
    chat_id = ""
    try:        
        data = json.loads(request.body.decode('utf-8'))
        chat_id = data['message']['chat']['id']
        user_id = data['message']['from']['id']
        message = data['message']['text']
        chat = Chat.objects.get(pk = chat_id)
    # If chat not in database
    except Chat.DoesNotExist:
        chat = Chat(chat_id = chat_id)
        chat.save()
    except Exception:
        return HttpResponse()

    # Set user language
    if chat.language == "ru":
        responses = ru
    else:
        responses = ua
    # Make commands and parameters case insensitive    
    message = message.lower()
    
    try:
        # Check command existance
        command = message.split()[0].split('@')[0]
        if not command in commands:
            return HttpResponse()

        # Statistics
        track(miscellaneous.key.BOTAN_TOKEN, user_id, {get_group_name_by_id(chat.group_id) : 1}, "Group") 
        track(miscellaneous.key.BOTAN_TOKEN, user_id, {}, command)

        # If command doesn't need timetable
        if command == "/start" or command == "/help":
            reply(chat_id, msg = responses['instructions'])
        elif command == "/bug" or command == "/idea":
            mail_admins('Bug or Idea', message)
            reply(chat_id, msg = responses['email_sent'])
        elif command == "/authors":
            reply(chat_id, msg = responses['authors'])
        elif command == "/week":
            reply(chat_id, msg = responses['week'].format(datetime.date.today().isocalendar()[1] % 2 + 1))
        elif command == "/time":
            reply(chat_id, msg = time)
        elif command == "/remind":
            chat.remind = not chat.remind
            chat.save()
            if chat.remind:
                reply(chat_id, responses['reminder_on'])
            else:
                reply(chat_id, responses['reminder_off'])
        elif command == "/changelang":
            if chat.language == "ru":
                chat.language = "ua"
                reply(chat_id, msg = ua['change_lang'])
            else:
                chat.language = "ru"
                reply(chat_id, msg = ru['change_lang'])
            chat.save()

        if command in no_timetable_commands:
            return HttpResponse()

        # If command require timetable
        if chat.group_id == 0:
            tt = TeacherTimetable(chat_id, message)
        else:
            tt = GroupTimetable(chat_id, message)

        # Check wrong parameter and access error
        if tt.is_wrong_parameter:
            return HttpResponse()

        #Command processing
        if command == "/setgroup": 
            tt.setgroup()
        elif command == "/setteacher": 
            tt.setteacher()
        elif command == "/tt":
            tt.tt()
        elif command == "/today":
            tt.today()
        elif command == "/tomorrow": 
            tt.tomorrow()
        elif command == "/now":
            tt.now()
        elif command == "/next":
            tt.next()
        elif command == "/where": 
            tt.where()
        elif command == "/who":
            tt.who()
        elif command == "/teacher":
            tt.teachertt()
    except:
        pass
    finally:
        return HttpResponse()
