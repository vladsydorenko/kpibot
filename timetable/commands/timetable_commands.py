from datetime import date
from django.conf import settings
from django.utils.translation import ugettext as _

from timetable.api_client import KPIHubAPIClient
from timetable.commands.base import TimetableTelegramCommand


class TodayCommand(TimetableTelegramCommand):
    command = '/today'
    validation_schema = {
        'required': [('groups', 'teachers'), 'week', 'day'],
        'optional': ['print_teacher']
    }

    def set_default_values(self):
        super().set_default_values()
        self.arguments['week'] = self.current_educational_week()
        self.arguments['day'] = date.today().weekday() + 1


class TomorrowCommand(TimetableTelegramCommand):
    command = '/tomorrow'
    validation_schema = {
        'required': [('groups', 'teachers'), 'week', 'day'],
        'optional': ['print_teacher']
    }

    def set_default_values(self):
        super().set_default_values()
        self.arguments['week'] = self.current_educational_week()
        self.arguments['day'] = date.today().weekday() + 2

        # If call this command on Sunday - get timetable for Monday of next week
        if self.arguments['day'] == 8:
            self.arguments['week'] = 2 - self.arguments['week']
            self.arguments['day'] = 1


class NowCommand(TimetableTelegramCommand):
    command = '/now'
    validation_schema = {
        'required': [('groups', 'teachers'), 'week', 'day', 'number'],
        'optional': ['print_teacher']
    }

    def set_default_values(self):
        super().set_default_values()
        self.arguments['week'] = self.current_educational_week()
        self.arguments['day'] = date.today().weekday() + 1
        self.arguments['number'] = self.current_lesson_number()


class WhoCommand(TimetableTelegramCommand):
    command = '/who'
    validation_schema = {
        'required': ['groups', 'week', 'day', 'number'],
    }

    def set_default_values(self):
        super().set_default_values()
        self.arguments['week'] = self.current_educational_week()
        self.arguments['day'] = date.today().weekday() + 1
        self.arguments['number'] = self.current_lesson_number()

    def process_timetable(self):
        lesson = self.timetable[str(self.arguments['week'])][str(self.arguments['day'])][str(self.arguments['number'])]

        if not lesson['teachers']:
            self.reply(_('В расписании не написано что это за преподаватель, так что для тебя он *Извините Пожалуйста*'))
        else:
            teachers_names = []
            for teacher_id in lesson['teachers']:
                teacher_object = KPIHubAPIClient.get_teacher(teacher_id)
                teachers_names.append(teacher_object['full_name'])
            self.reply('\n'.join(teachers_names))


class WhereCommand(TimetableTelegramCommand):
    command = '/where'
    validation_schema = {
        'required': ['groups', 'week', 'day', 'number'],
    }

    def set_default_values(self):
        super().set_default_values()
        self.arguments['week'] = self.current_educational_week()
        self.arguments['day'] = date.today().weekday() + 1
        self.arguments['number'] = self.current_lesson_number()

    def process_timetable(self):
        lesson = self.timetable[str(self.arguments['week'])][str(self.arguments['day'])][str(self.arguments['number'])]

        if not lesson['rooms']:
            self.reply(_('В расписании нет аудитории для текущей пары.'))
        else:
            for room_id in lesson['rooms']:
                room_object = KPIHubAPIClient.get_room(room_id)
                building_object = KPIHubAPIClient.get_building(room_object['building'])
                self.reply(_('Сейчас пара в аудитории *{}*. Я скину тебе расположение корпуса').format(
                    room_object['full_name']))
                settings.BOT.send_location(self.chat.id,
                                           latitude=float(building_object['latitude']),
                                           longitude=float(building_object['longitude']))


class TeacherCommand(TimetableTelegramCommand):
    command = '/teacher'
    validation_schema = {
        'required': ['teachers'],
        'optional': ['week', 'day', 'number']
    }

    def set_default_values(self):
        pass


class TTCommand(TimetableTelegramCommand):
    command = '/tt'
    validation_schema = {
        'required': [('groups', 'teachers')],
        'optional': ['print_teacher', 'week', 'day', 'number']
    }
