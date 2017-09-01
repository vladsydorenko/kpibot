import json

from django.conf import settings
from django.http import HttpResponse
from django.utils.translation import activate
import telegram

from timetable.exceptions import ParsingError, ValidationError, StopExecution
from timetable.constants import EXCEPTION_MESSAGE
from timetable.models import Chat
bot = settings.BOT


class LocaleMiddleware:
    """Switch locale to chat language"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            data = json.loads(request.body.decode('utf-8'))
            # Edited messages has different key in request payload, so we need to handle it
            chat_id = data['message']['chat']['id'] if 'message' in data else data['edited_message']['chat']['id']
            try:
                chat = Chat.objects.get(pk=chat_id)
            except Chat.DoesNotExist:
                activate("ru")
            else:
                activate(chat.language)
        except:
            return HttpResponse()

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
        # Edited messages has different key in request payload, so we need to handle it
        chat_id = data['message']['chat']['id'] if 'message' in data else data['edited_message']['chat']['id']

        try:
            if exception.__class__ in (ParsingError, ValidationError):
                bot.send_message(chat_id=chat_id, text=str(exception))
            elif exception.__class__ != StopExecution:
                bot.send_message(chat_id=chat_id, text=EXCEPTION_MESSAGE)

                # Send traceback to developer
                import traceback
                bot.send_message(chat_id=settings.LOG_CHAT_ID, text=traceback.format_exc())
                bot.send_message(chat_id=settings.LOG_CHAT_ID, text="{}".format(json.dumps(data, indent=4)))
        # User might block bot, so we can't send him message about exception, we need to just ignore it.
        except telegram.error.Unauthorized:
            pass

        return HttpResponse()
