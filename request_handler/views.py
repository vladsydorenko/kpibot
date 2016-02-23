# -*- coding: UTF-8 -*-
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from request_handler.models import Chat
from django.http import HttpResponse

import json
import datetime
#Support different languages (ru, ua)
from miscellaneous.lang import ru, ua
from miscellaneous.botan import track
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
        chat = Chat.objects.get(pk=chat_id)
    # If chat not in database
    except Chat.DoesNotExist:
        chat = Chat(chat_id=chat_id)
        chat.save()
    except Exception:
        return HttpResponse()

    # Set user language
    responses = ru if chat.language == "ru" else ua
    # Make commands and parameters case insensitive
    message = message.lower()

    try:
        # Check command existance
        command = message.split()[0].split('@')[0]
        if command not in commands:
            return HttpResponse()

        # Statistics
        track(miscellaneous.key.BOTAN_TOKEN, user_id, {get_group_name_by_id(chat.group_id): 1}, "Group")
        track(miscellaneous.key.BOTAN_TOKEN, user_id, {}, command)

        # If command doesn't need timetable
        if command == "/start" or command == "/help":
            reply(chat_id, msg=responses['instructions'])
        elif command == "/authors":
            reply(chat_id, msg=responses['authors'])
        elif command == "/week":
            reply(chat_id, msg=responses['week'].format(2 - datetime.date.today().isocalendar()[1] % 2))
        elif command == "/time":
            reply(chat_id, msg=time)
        elif command == "/changelang":
            if chat.language == "ru":
                chat.language = "ua"
                reply(chat_id, msg=ua['change_lang'])
            else:
                chat.language = "ru"
                reply(chat_id, msg=ru['change_lang'])
            chat.save()

        if command in no_timetable_commands:
            return HttpResponse()

        # If command require timetable
        tt = TeacherTimetable(chat_id, message) if chat.group_id == -1 else GroupTimetable(chat_id, message)

        # Check wrong parameter and access error
        if tt.is_wrong_parameter:
            return HttpResponse()

        #Command processing
        getattr(tt, command[1:])()
    except:
        pass
    finally:
        return HttpResponse()

@csrf_exempt
def test(request):
    #try:
    #    tt = GroupTimetable(111791142, "/who")
    #    tt.who()
    #except Exception:
    #    import traceback
    #    reply(111791142, msg=traceback.format_exc())
    #finally:
    return HttpResponse()
