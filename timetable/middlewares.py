import json

from django.conf import settings
from django.http import HttpResponse
from django.utils.translation import activate

from timetable.models import Chat

bot = settings.BOT

class LocaleMiddleware:
    """Switch locale to chat language"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        data = json.loads(request.body.decode('utf-8'))
        chat_id = data['message']['chat']['id']
        try:
            chat = Chat.objects.get(pk=chat_id)
            activate(chat.language)
        except Chat.DoesNotExist:
            activate("ru")

        response = self.get_response(request)
        return response


class ErrorHandlingMiddleware:
    """Send all error messages to admin"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        data = json.loads(request.body.decode('utf-8'))
        chat_id = data['message']['chat']['id']
        bot.sendMessage(chat_id=chat_id, text="""Из-за кривых рук моего
разработчика случилась нередвиденная ошибка, но он уже об этом знает и скоро
всё исправит. Если ты хочешь пнуть его лично, то пиши @vladsydorenko""")
        # Send traceback to developer
        import traceback
        bot.sendMessage(chat_id=settings.LOG_CHAT_ID,
                        text=traceback.format_exc())
        bot.sendMessage(chat_id=settings.LOG_CHAT_ID,
                        text=json.dumps(data, indent=4))
        return HttpResponse()
