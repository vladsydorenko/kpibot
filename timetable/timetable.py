import requests
from collections import defaultdict

from django.conf import settings
from django.utils.translation import ugettext as _

from timetable.constants import LESSON_TYPES, WEEK_DAYS
from timetable.entities import APIEntity, Group, Teacher
from timetable.exceptions import StopExecution
from timetable.models import Chat
from timetable.parameters import Parameters


class KPIHubTimetable:
    """Base class for interacting with timetable API.
    Takes Chat object, entity (Group or Teacher object), Parameters object,
    and sends corresponding message to user.
    """

    def __init__(self, chat: Chat, entity: APIEntity, parameters: Parameters):
        self.chat = chat
        self.entity = entity
        self.parameters = parameters

        # Prepare data
        self.timetable = self._get_timetable()

    def execute(self, command):
        # If API returned empty array
        if not self.timetable:
            if command == "/next":
                self.timetable = self._get_next_lesson()
            else:
                self._send(_("Пар нет, наслаждайся."))
                return

        # Transform timetable dictionary to readable form
        result = defaultdict(lambda: defaultdict(list))
        for lesson in self.timetable:
            result[lesson['week']][lesson['day']].append(
                self._format_lesson(lesson))

        # Send prepared messages
        for week_number, week_timetable in result.items():
            for day, lessons_list in week_timetable.items():
                header = "{} ({} {}):\n".format(WEEK_DAYS[day], week_number,
                                                _("неделя"))
                self._send(header + '\n'.join(lessons_list))

    def _format_lesson(self, lesson: dict):
        """Format API lesson response to readable form"""
        lesson_type = " ({})".format(LESSON_TYPES.get(lesson['type'], ""))
        rooms_list = ", ".join(lesson['rooms_full_names']) if lesson['rooms']\
            else _("расположение неизвестно")

        formatted_lesson = "*{}*: {}{} - {}".format(lesson['number'],
                                                    lesson['discipline_name'],
                                                    lesson_type,
                                                    rooms_list)
        # If "T" parameter has been passed, add teachers names to response.
        if hasattr(self.parameters, 'print_teacher'):
            if lesson['teachers']:
                formatted_lesson += "— {}\n".join(lesson['teachers_short_names'])
            else:
                formatted_lesson += "— {}\n".format(_("неизвестно"))
        return formatted_lesson

    def _get_next_lesson(self) -> list:
        """Custom function for handling not trivial cases for '/next' command
        """
        # There are 3 possible scenarios:
        # 1. There is no next lesson, but there are lessons today in future.
        query_parameters = {
            'week': self.parameters.week,
            'day': self.parameters.day,
            'number__gt': self.parameters.number,
        }
        self.timetable = self._get_timetable(query_parameters)
        if not self.timetable:
            # 2. There are no lessons today, and we need to switch to
            #    next day (but it can be saturday, or sunday, so we
            #    need to consider it)
            # Check current week
            query_parameters = {
                'week': self.parameters.week,
                'day__gt': self.parameters.day,
            }
            self.timetable = self._get_timetable(query_parameters)
            if not self.timetable:
                # Check next week
                query_parameters = {
                    'week': 3 - self.parameters.week,
                }
                self.timetable = self._get_timetable(query_parameters)

        if self.timetable:
            self.timetable = self.timetable[:1]  # Get only first lesson
        else:
            # 3. Timetable for this group/teacher is empty.
            self._send(_("К сожалению, для Вас в базе нет расписания :("))
            raise StopExecution()

    def _get_timetable(self, query_parameters={}) -> list:
        if not query_parameters:
            possible_query_parameters = ['week', 'day', 'number']

            for parameter in possible_query_parameters:
                if hasattr(self.parameters, parameter):
                    query_parameters[parameter] = getattr(self.parameters,
                                                          parameter)
        if isinstance(self.entity, Group):
            query_parameters['groups'] = self.entity.resource_id
        elif isinstance(self.entity, Teacher):
            query_parameters['teachers'] = self.entity.resource_id
        query_parameters['limit'] = 100

        response = requests.get(settings.TIMETABLE_URL + '/lessons',
                                query_parameters)

        return response.json()['results']

    def _send(self, text):
        """Shortcut for sending text response to user"""
        settings.BOT.sendMessage(self.chat.id, text=text,
                                 parse_mode='Markdown')
