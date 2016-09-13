import json
from datetime import date

from django.views.decorators.http import require_http_methods
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

from kpibot.utils import botan, constants, bot
from timetable.models import Chat
from timetable.parameters import Parameters
from timetable.timetable import Timetable


@csrf_exempt
@require_http_methods(["POST"])
def index(request):
    data = json.loads(request.body.decode('utf-8'))
    message = data['message'] if 'message' in data\
        else data['edited_message']
    chat_id = message['chat']['id']
    user_id = message['from']['id']
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
    # TODO: Implement /setgroup and /setteacher

    if command in constants.NO_TIMETABLE_COMMANDS:
        return HttpResponse()

    parameters = Parameters(command, message.split[1:])
    if parameters.is_valid():
        pass  # TODO: Implement
    else:
        # Send list of all errors
        bot.sendMessage(chat_id, text='\n'.join(parameters.errors))
