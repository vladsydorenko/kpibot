import json

from django.conf import settings
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from timetable import constants
from timetable import commands
from timetable.models import Chat

bot = settings.BOT

command_objects = {
    #'/changelang': commands.ChangeLanguageCommand,
    '/help': commands.HelpCommand,
    '/now': commands.NowCommand,
    '/setgroup': commands.SetgroupCommand,
    '/setteacher': commands.SetteacherCommand,
    '/start': commands.HelpCommand,
    '/teacher': commands.TeacherCommand,
    '/time': commands.TimeCommand,
    '/today': commands.TodayCommand,
    '/tomorrow': commands.TomorrowCommand,
    '/tt': commands.TTCommand,
    '/week': commands.WeekCommand,
    '/where': commands.WhereCommand,
    '/who': commands.WhoCommand
}


@method_decorator(csrf_exempt, name='dispatch')
class CommandDispatcherView(View):
    def post(self, request):
        data = json.loads(request.body.decode('utf-8'))
        try:
            # Edited messages has different key in request payload, so we need to handle it
            message = data['message'] if 'message' in data else data['edited_message']
        except KeyError:
            # Bot can receive messages that it shouldn't process (like new participant in group chat),
            # so we need to just ignore such messages
            return HttpResponse()

        chat_id = message['chat']['id']
        self.chat, _ = Chat.objects.get_or_create(id=chat_id)

        try:
            # Check that user sent text, not image or anything else.
            message = message['text'].lower()
        except KeyError:
            return HttpResponse()

        # Check if we can process such command
        command = message.split()[0].split('@')[0]
        if command not in command_objects.keys():
            return HttpResponse()

        # If command doesn't need timetable
        param_tokens = message.split()[1:]
        command_objects[command](param_tokens, self.chat).run()

        return HttpResponse()
