import json
from datetime import date

from django.http import HttpResponse
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from kpibot.utils.exceptions import StopExecution
from kpibot.utils import botan, constants, bot
from timetable.models import Chat
from timetable.entities import Group, Teacher
from timetable.parameters import Parameters
from timetable.timetable import KPIHubTimetable


@csrf_exempt
@require_http_methods(["POST"])
def index(request):
    data = json.loads(request.body.decode('utf-8'))
    message = data['message'] if 'message' in data\
        else data['edited_message']
    chat_id = message['chat']['id']
    message = message['text'].lower()

    chat, created = Chat.objects.get_or_create(pk=chat_id)

    # Check command existance
    command = message.split()[0].split('@')[0]
    if command not in constants.ALLOWED_COMMANDS:
        return HttpResponse()

    # Statistics
    # botan.track(settings.BOTAN_TOKEN, user_id,
    #             {get_group_name_by_id(chat.group_id): 1}, "Group")

    # If command doesn't need timetable
    if command == "/start" or command == "/help":
        bot.sendMessage(chat_id, text=_(constants.HELP_TEXT),
                        parse_mode="Markdown")
    elif command == "/authors":
        bot.sendMessage(chat_id, text=_(constants.AUTHORS),
                        parse_mode="Markdown")
    elif command == "/week":
        current_week = 2 - date.today().isocalendar()[1] % 2
        bot.sendMessage(chat_id,
                        text=_("Сейчас {0} неделя".format(current_week)))
    elif command == "/time":
        bot.sendMessage(chat_id, text=constants.TIME)
    elif command == "/changelang":
        chat.language = "uk" if chat.language == "ru" else "ru"
        chat.save()
        bot.sendMessage(chat_id, text=_("Язык бота был изменён"))

    if command in constants.NO_TIMETABLE_COMMANDS:
        return HttpResponse()

    # If we need to get information from API.
    parameters = Parameters(command, message.split()[1:])
    if parameters.is_valid():
        if command == "/setgroup":
            group = Group(name=parameters.group_name)
            chat.category = 'group'
            chat.resource_id = group.id
            chat.save()
            bot.sendMessage(chat_id, text=_("Я запомнил Вашу группу!"))
        elif command == "/setteacher":
            teacher = Teacher(name=parameters.teachers_name)
            chat.category = 'teacher'
            chat.resource_id = teacher.id
            chat.save()
            bot.sendMessage(chat_id, text=_("Я запомнил Ваше имя!"))
        else:
            try:
                # If group was passed as parameter, use this group
                if hasattr(parameters, 'group_name'):
                    entity = Group(name=parameters.group_name)
                else:  # Otherwise - use chat group (it should be set)
                    entity = chat.get_entity()
                timetable = KPIHubTimetable(chat, entity, parameters)
                timetable.run(command)
            except StopExecution:
                pass
    else:
        # Send list of all validation errors
        bot.sendMessage(chat_id, text='\n'.join(parameters.errors))
    return HttpResponse()
