import json

from django.conf import settings
from django.http import HttpResponse
from django.utils.translation import activate

from timetable.models import Chat


class LocaleMiddleware(object):
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


class LoggingMiddleware(object):
    """Send all error messages to admin"""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = HttpResponse()
        try:
            response = self.get_response(request)
        except:
            import traceback
            settings.BOT.sendMessage(chat_id=settings.LOG_CHAT_ID,
                                     text=traceback.format_exc())
            settings.BOT.sendMessage(chat_id=settings.LOG_CHAT_ID,
                                     text=request.body.decode())
        finally:
            return response
