import requests

from django.conf import settings
from django.utils.translation import ugettext as _

from kpibot.utils import bot
from kpibot.utils.constants import LESSON_TYPES
from timetable.models import Chat
from timetable.entity import APIEntity, Group, Teacher
from timetable.parameters import Parameters


class Timetable:
    """Base class for interacting with timetable API.
    Takes Chat object, entity (Group or Teacher object), Parameters object,
    and sends corresponding message to user.
    """
    def __init__(self, chat: Chat, entity: APIEntity, parameters: Parameters):
        self.chat = chat
        self.entity = entity
        self.command = command
        self.parameters = parameters

        # Prepare data
        self.timetable = self._get_timetable()

    def run(self, command):
        # If API returned empty array
        if not self.timetable:
            if command == "/next":
                pass  # TODO: Implement
            else:
                self._send(_("Пар нет, наслаждайся."))
                return
        
        # Transform timetable dictionary to readable form
        week_days = [_("Понедельник"), _("Вторник"), _("Среда"),
                     _("Четверг"), _("Пятница"), _("Суббота")]
        result = {
            week: {
                week_day: "" for week_day in week_days
            } for week in [1, 2]
        }
        for lesson in self.timetable:
            result[lesson['week']][lesson['day']] += "*{}*: {}{} - {}".format(
                lesson['number'],
                lesson['discipline_name'],
                " ({})".format(LESSON_TYPES[lesson['type']])\
                               if lesson['type'] else "",
                ", ".join(lesson['rooms_full_names']) if lesson['rooms']
                    else _("расположение неизвестно\n"))
            # If "T" parameter has been passed
            if self.parameters.print_teacher:
                if lesson['teachers']:
                    result[lesson['day']] += "— {}\n".join(
                        lesson['teachers_short_names'])
                else:
                    result[lesson['day']] += "— {}\n".format(_("неизвестно"))

        # Send prepared messages
        for week_number, week_timetable in result.items():
            for day, text in week_timetable:
                if text:
                    text = "{} ({} {}):\n".format(day, week_number,
                        _("неделя")) + text
                    self._send(text)



    def _get_timetable(self) -> list:
        possible_query_parameters = ['week', 'day', 'number']
        query_parameters = {}

        for parameter in possible_query_parameters:
            if hasattr(self.parameters, parameter):
                query_parameters[parameter] = getattr(self.parameters,
                                                      parameter)

        if isinstance(self.entity, Group):
            query_parameters['groups'] = self.entity.id
        elif isinstance(self.entity, Teacher):
            query_parameters['teachers'] = self.entity.id

        response = requests.get(settings.TIMETABLE_URL + '/lessons.json',
                                query_parameters)

        return response.json()['results']

    def _send(self, text):
        """Shortcut for sending text response to user"""
        bot.sendMessage(self.chat_id, text=text, parse_mode='Markdown')

    # def update(self, update_message_id):
    #     result = self._show_day(dont_send=True)
    #     inline_keyboard = []
    #     if self.day == 6:
    #         next_day = 1
    #         next_week = 3 - self.week
    #     else:
    #         next_day = self.day + 1
    #         next_week = self.week
    #     next_data = "/update w{} {}".format(next_week, days[next_day][0])

    #     if self.day == 1:
    #         previous_day = 6
    #         previous_week = 3 - self.week
    #     else:
    #         previous_day = self.day - 1
    #         previous_week = self.week
    #     previous_data = "/update w{} {}".format(previous_week, days[previous_day][0])
    #     row = [{'text': "<<", 'callback_data': previous_data},
    #            {'text': ">>", 'callback_data': next_data}]
    #     inline_keyboard.append(row)
    #     utils.update(self.chat_id, update_message_id, result, inline_keyboard)
