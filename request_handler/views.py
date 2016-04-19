# -*- coding: UTF-8 -*-
import json

from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.conf import settings

from request_handler.models import Chat

from miscellaneous.lang import localization
from miscellaneous.botan import track
from miscellaneous.arrays import commands, no_timetable_commands, time
from miscellaneous.utils import reply, get_group_name_by_id, get_current_week, send_log
from request_handler.timetable import GroupTimetable, TeacherTimetable


@csrf_exempt
@require_http_methods(["POST"])
@send_log
def index(request):
    chat = None
    message = ""
    chat_id = ""
    try:
        data = json.loads(request.body.decode('utf-8'))
        chat_id = data['message']['chat']['id']
        user_id = data['message']['from']['id']
        message = data['message']['text']
        chat = Chat.objects.get(pk=chat_id)
    # If chat not in database
    except Chat.DoesNotExist:
        chat = Chat(chat_id=chat_id)
        chat.save()
    except ValueError:
        data = request.body.decode('utf-8').replace(',{', ',"random_name":{')
        data = json.loads(data)
        upd_message_id = data['callbackquery']['message']['messageid']
        message = data['callbackquery']['data']
        chat_id = data['callbackquery']['message']['chat']['id']
        chat = Chat.objects.get(pk=chat_id)

    # Set user language
    responses = localization[chat.language]
    # Make commands and parameters case insensitive
    message = message.lower()
    # Check command existance
    command = message.split()[0].split('@')[0]
    if command not in commands:
        return HttpResponse()

    # Statistics
    track(settings.BOTAN_TOKEN, user_id, {get_group_name_by_id(chat.group_id): 1}, "Group")
    track(settings.BOTAN_TOKEN, user_id, {"Group:": get_group_name_by_id(chat.group_id)}, command)

    # If command doesn't need timetable
    if command == "/start" or command == "/help":
        reply(chat_id, msg=responses['instructions'])
    elif command == "/authors":
        reply(chat_id, msg=responses['authors'])
    elif command == "/week":
        reply(chat_id, msg=responses['week'].format(get_current_week()))
    elif command == "/time":
        reply(chat_id, msg=time)
    elif command == "/changelang":
        chat.language = "ua" if chat.language == "ru" else "ru"
        chat.save()
        reply(chat_id, msg=localization[chat.language]['change_lang'])

    if command in no_timetable_commands:
        return HttpResponse()

    # If command require timetable
    tt = TeacherTimetable(chat_id, message) if chat.group_id == -1 else GroupTimetable(chat_id, message)

    # Check wrong parameter and access error
    if tt.is_wrong_parameter:
        return

    if command == "/update":
        tt.update(upd_message_id)
    # Command processing
    getattr(tt, command[1:])()
