import re
import requests
import datetime

from django.conf import settings

import miscellaneous.utils as utils
from miscellaneous.utils import StopExecution
from miscellaneous.lang import localization
from miscellaneous.utils import reply, get_current_lesson_number,\
    transliterate, get_current_week
from miscellaneous.arrays import commands, types, days

from request_handler.models import Chat, Group


class Timetable(object):

    def __init__(self, chat_id, message):
        self.group_id = 0
        self.week = 0
        self.day = 0
        self.lesson_number = 0
        self.teacher_id = 0
        self.teacher_query = ""
        self.show_teacher = False
        self.show_full_week = False
        self.parameters = []
        self.is_wrong_parameter = True

        self.timetable = {}
        self.responses = {}

        self.chat_id = chat_id

        # Set user language
        chat = Chat.objects.get(pk=chat_id)
        self.responses = localization[chat.language]

        # Read parameters from message
        command = message.split()[0].split('@')[0]
        parameters_number = len(message.split()) - 1
        self._read_parameters(message)
        self._validate_parameters(command, parameters_number)

        # Set current time
        if command != '/tt':
            self.week = get_current_week()
            self.day = datetime.date.today().weekday() + 1
            self.lesson_number = utils.get_current_lesson_number()

    def _read_parameters(self, message):
        """
        Transform command parameters to class fields
        """
        if len(message.split()) > 1:
            for token in message.split()[1:]:
                self.parameters.append(token)
                if re.match("[A-zА-яіє]{2,4}-?[A-zА-яіє]{0,2}[0-9]{2,3}[A-zА-яіє]?\(?[A-zА-яіє]*\)?", token):
                    group_name = transliterate(token)
                    if '-' not in token:
                        number_position = re.search("\d", token).start()
                        group_name = group_name[:number_position] + '-' + group_name[number_position:]

                    self.group_id = utils.get_group_id_by_name(group_name)
                    if self.group_id == -2:
                        self.group_name = group_name
                        self.parameters.pop()
                elif re.match("[w]{1,1}[1|2]{1,1}", token):
                    self.week = int(token[1])
                elif re.match("[w]{1,1}", token):
                    self.week = get_current_week()
                elif utils.get_week_day(token):
                    self.day = utils.get_week_day(token)
                elif re.match("[t]{1,1}", token):
                    self.show_teacher = True
                elif re.match("[0-9]+", token):
                    if int(token) < 7:
                        self.lesson_number = int(token)
                    else:
                        self.teacher_id = int(token)
                elif re.match("[A-zА-яіє]+", token):
                    self.teacher_query += token if not self.teacher_query else " " + token
                else:
                    reply(self.chat_id, msg=self.responses['wrong_parameter'])
                    self.is_wrong_parameter = True

    def _validate_parameters(self, command, parameters_number):
        if parameters_number > commands[command]:
            reply(self.chat_id, self.responses['wrong_parameters_number'])
        elif command != "/tt" and (self.week != 0 or self.day != 0):
            reply(self.chat_id, msg=self.responses['wrong_parameter'])
        elif (command != "/setteacher" and command != "/teacher") and (self.teacher_query or self.teacher_id):
            reply(self.chat_id, msg=self.responses['wrong_parameter'])
        elif (command == "/setteacher" or command == "/teacher") and not self.teacher_id and not self.teacher_query:
            reply(self.chat_id, msg=self.responses['no_required_parameter'])
        elif command == "/setgroup" and self.group_id == -1:
            reply(self.chat_id, msg=self.responses['unknown_group'])
        elif command == "/setgroup" and self.group_id == 0:
            reply(self.chat_id, msg=self.responses['no_required_parameter'])
        elif self.group_id == -2:
            query = Group.objects.filter(group_name__icontains=self.group_name + "(")
            keyboard = []
            for item in query:
                row = ["{0} {1} ".format(command, item.group_name) + " ".join(self.parameters)]
                keyboard.append(row)
            reply(self.chat_id, msg=self.responses['same_group'], keyboard=keyboard)
        elif command == "/tt" and self.day == 0:
            self.show_full_week = True
            self.is_wrong_parameter = False
        else:
            self.is_wrong_parameter = False

    def _check_day(self):
        # Custom reply for sunday
        if self.day == 7:
            reply(self.chat_id, self.responses['sunday'])
            return False

        # Check day existance
        try:
            day = self.timetable[self.week][self.day]
            if day == {}:
                if not self.show_full_week:
                    reply(self.chat_id, msg=self.responses['no_lessons_for_this_day'])
                return False
        except KeyError:
            if not self.show_full_week:
                reply(self.chat_id, msg=self.responses['get_tt_error'])
            return False

        return True

    def _show_day(self, use_inline=False):
        """
        Shows timetable for whole day
        """
        if not self._check_day():
            return

        # Add week day as title
        result = "*{}*\n_{}_\n".format(self.responses['week'].format(get_current_week()),
                                       self.responses['week_days'][self.day])
        # Generate message body
        for lesson_number in self.timetable[self.week][self.day]:
            lesson = self.timetable[self.week][self.day][lesson_number]
            result += "*{}*: {}{} - {}".format(lesson_number,
                                                 lesson['discipline']['name'],
                                                 " (%s)" % types[lesson['type']] if lesson['type'] else "",
                                                 utils.generate_rooms_string(lesson['rooms'], self.responses))
            # If "T" parameter has been passed
            if self.show_teacher:
                if lesson['teachers']:
                    for teacher in lesson['teachers']:
                        result += "— " + teacher['name'] + "\n"
                else:
                    result += "— " + self.responses['no_teacher'] + "\n"

        if use_inline:
            inline_keyboard = []
            if self.day == 6:
                next_day = 1
                next_week = 3 - self.week
            else:
                next_day = self.day + 1
                next_week = self.week
            next_data = "/tt w{} {}".format(next_week, days[next_day][0])

            if self.day == 1:
                previous_day = 6
                previous_week = 3 - self.week
            else:
                previous_day = self.day - 1
                previous_week = self.week
            previous_data = "/tt w{} {}".format(previous_week, days[previous_day][0])
            row = [{'text': "<<", 'callback_data': previous_data},
                   {'text': ">>", 'callback_data': next_data}]
            inline_keyboard.append(row)
            reply(self.chat_id, msg=result, inline_keyboard=inline_keyboard)
        else:
            reply(self.chat_id, msg=result)

    def _show_lesson(self, show_time_to_end=False):
        """
        Shows only one lesson
        """
        if not self._check_day():
            return

        # Generating message body
        try:
            lesson = self.timetable[self.week][self.day][self.lesson_number]
        except KeyError:
            reply(self.chat_id, msg=self.responses['no_lesson'])
            return

        result = self.responses['week_days'][self.day] + ":\n" + \
            str(self.lesson_number) + ": " + lesson['discipline']['name'] + " - " + \
            utils.generate_rooms_string(lesson['rooms'], self.responses)

        # Show teacher
        if self.show_teacher:
            if lesson['teachers']:
                for teacher in lesson['teachers']:
                    result += "— " + teacher['name'] + "\n"
            else:
                result += "— " + self.responses['no_teacher'] + "\n"

        # Add showing time to the end or lesson for /now command
        if show_time_to_end:
            time_to_end = utils.get_time_to_lesson_end(self.lesson_number)
            result += self.responses['minutes_left'].format(time_to_end)

        reply(self.chat_id, msg=result)

    def now_has_lesson(self):
        return get_current_lesson_number() in self.timetable[self.week][self.day]

    def now(self):
        self._show_lesson(show_time_to_end=True)

    def next(self):
        self.lesson_number += 1

        # For example, for friday after lessons
        if self.day in self.timetable[self.week] and self.timetable[self.week][self.day]\
                and self.lesson_number > sorted(self.timetable[self.week][self.day].keys())[-1]:
            self.lesson_number = 0
            self.day += 1

        # Get day with lessons (for satuday, sunday, etc.)
        while self.day not in self.timetable[self.week] or self.timetable[self.week][self.day] == {}:
            self.lesson_number = 0
            if self.day == 7:
                self.day = 1
                self.week = 3 - self.week
            else:
                self.day += 1

        while self.lesson_number not in self.timetable[self.week][self.day]:
            self.lesson_number += 1
        self._show_lesson()

    def where(self):
        if not self._check_day():
            return

        # Check lesson existance
        if self.lesson_number not in self.timetable[self.week][self.day]:
            reply(self.chat_id, msg=self.responses['no_lesson'])
            return

        lesson = self.timetable[self.week][self.day][self.lesson_number]

        # Check if room set in timetable
        if not lesson['rooms']:
            reply(self.chat_id, msg=self.responses['no_room'])
            return

        coordinates = {}
        for room in lesson['rooms']:
            coordinates['longitude'] = float(room['building']['longitude'])
            coordinates['latitude'] = float(room['building']['latitude'])
            reply(self.chat_id, location=coordinates)
        reply(self.chat_id, result=utils.generate_rooms_string(lesson['rooms'], self.responses))

    def today(self):
        self._show_day()

    def tomorrow(self):
        if self.day == 7:
            self.day = 1
            self.week = 3 - self.week
        else:
            self.day += 1

        self._show_day()

    def tt(self):
        # To specify lesson number
        if self.lesson_number != 0:
            if self.day != 0 and self.week != 0:
                self._show_lesson()
                return
            else:
                reply(self.chat_id, msg=self.responses['no_week_or_day'])
                return

        week_range = [self.week]
        if self.week == 0:
            if self.day != 0:
                reply(self.chat_id, msg=self.responses['no_week'])
                return
            week_range = [1, 2]

        for self.week in week_range:
            reply(self.chat_id, msg="*Week #%i*:" % self.week)
            if self.day == 0:
                for self.day in range(1, 7):
                    self._show_day()
                self.day = 0
            else:
                self._show_day()

    def setgroup(self):
        c = Chat(chat_id=self.chat_id,
                 group_id=self.group_id,
                 teacher_id=0)
        c.save()
        reply(self.chat_id, msg=self.responses['setgroup_success'])

    def setteacher(self):
        if self.teacher_query:
            self.answer_teacher_query()
        else:
            self.setteacher_id()

    def answer_teacher_query(self, is_teachertt=False):
        raw_response = requests.get(settings.TIMETABLE_URL + "teachers/?search=%s" % self.teacher_query)

        # Check teacher existance
        if raw_response.status_code != 200:
            reply(self.chat_id, self.responses['unknown_teacher'])
            return

        # List all teachers that satisfy requirements
        response = raw_response.json()
        teachers = response['results']
        if response['count'] == 1:
            self.teacher_id = teachers[0]['id']
            if is_teachertt:
                self.show_teacher_tt()
            else:
                self.setteacher_id()
        else:
            keyboard = []
            if is_teachertt:
                result = self.responses['teacher_tt']
            else:
                result = self.responses['setteacher_filter'].format(self.teacher_query)
            for teacher in teachers:
                row = []
                if is_teachertt:
                    row.append("/teacher %i" % teacher['id'])
                else:
                    row.append("/setteacher %i" % teacher['id'])
                keyboard.append(row)
                result += teacher['name'] + ' - ' + str(teacher['id']) + '\n'
            reply(self.chat_id, msg=result, keyboard=keyboard)

    def setteacher_id(self):
        c = Chat(chat_id=self.chat_id,
                 group_id=-1,
                 teacher_id=self.teacher_id)
        c.save()
        reply(self.chat_id, msg=self.responses['setteacher_success'])

    def show_teacher_tt(self):
        tt = TeacherTimetable(self.chat_id, '/tt', teacher_id=self.teacher_id)
        tt.tt()

    def day_test(self):
        self._show_day(use_inline=True)


class GroupTimetable(Timetable):

    def __init__(self, chat_id, message):
        try:
            super().__init__(chat_id, message)
            if self.is_wrong_parameter:
                raise StopExecution

            # Check if group was set (by /setgroup or passed as parameter)
            if self.group_id == 0:
                chat = Chat.objects.get(pk=chat_id)
                self.group_id = chat.group_id

                if self.group_id == 0:
                    reply(self.chat_id, msg=self.responses['empty_group'])
                    self.is_wrong_parameter = True
                    raise StopExecution

            # Get group timetable
            raw_response = requests.get(settings.TIMETABLE_URL + "groups/%i/timetable.json" % self.group_id)
            if raw_response.status_code == 200:
                response = raw_response.json()
                self.timetable = utils.prettify(response['data'])
            else:
                reply(self.chat_id, msg=self.responses['no_timetable_for_group'])
                self.is_wrong_parameter = True
        except StopExecution:
            pass

    def who(self):
        # Check lesson existance
        self._check_day()
        if self.lesson_number not in self.timetable[self.week][self.day]:
            reply(self.chat_id, msg=self.responses['no_lesson'])

        lesson = self.timetable[self.week][self.day][self.lesson_number]

        # Check if teachers set in timetable
        if not lesson['teachers']:
            reply(self.chat_id, msg=self.responses['no_teacher'])

        result = ""
        for teacher in lesson['teachers']:
            result += teacher['full_name'] + "\n"

        reply(self.chat_id, msg=result)

    def teacher(self):
        if self.teacher_query:
            self.answer_teacher_query(is_teachertt=True)
        else:
            self.show_teacher_tt()


class TeacherTimetable(Timetable):

    def __init__(self, chat_id, message, teacher_id=None):
        try:
            super().__init__(chat_id, message)
            if self.is_wrong_parameter:
                raise StopExecution

            if teacher_id:
                self.teacher_id = teacher_id
            else:
                command = message.split()[0].split('@')[0]
                if self.show_teacher or (self.group_id != 0 and command != "/setgroup"):
                    reply(self.chat_id, msg=self.responses['wrong_parameter_for_teacher'])
                    self.is_wrong_parameter = True
                    raise StopExecution

                if self.teacher_id == 0:
                    chat = Chat.objects.get(pk=chat_id)
                    self.teacher_id = chat.teacher_id

            # Get teacher timetable
            raw_response = requests.get(settings.TIMETABLE_URL + "teachers/%i/timetable.json" % self.teacher_id)
            if raw_response.status_code == 200:
                response = raw_response.json()
                self.timetable = response['data']
                self.timetable = utils.prettify(self.timetable)
            else:
                if command not in ['/setgroup', '/setteacher']:
                    reply(self.chat_id, msg=self.responses['get_tt_error'])
                    self.is_wrong_parameter = True

        except StopExecution:
            pass

    def who(self):
        """
        /who command isn't allowed in teachers mode. So we overload it, to send error
        """
        reply(self.chat_id, msg=self.responses['wrong_command_for_tm'])
