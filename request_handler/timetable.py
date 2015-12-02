from request_handler.models import Chat, Group
# System libs
import re
import requests
import datetime

# Own modules
import miscellaneous.utils as utils
from miscellaneous.utils import StopExecution, TIMETABLE_URL
from miscellaneous.lang import ru, ua
from miscellaneous.utils import reply, get_current_lesson_number, transliterate
from miscellaneous.arrays import pairs, commands, types


class Timetable(object):

    def __init__(self, chat_id, message):
        self.chat_id = 0
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
        if chat.language == "ru":
            self.responses = ru
        else:
            self.responses = ua

        # Read parameters from message
        command = message.split()[0].split('@')[0]
        parameters_number = len(message.split()) - 1
        self.__read_parameters(message)
        self.__check_parameters(command, parameters_number)

        # Set current time
        if command != '/tt':
            self.week = datetime.date.today().isocalendar()[1] % 2 + 1
            self.day = datetime.date.today().weekday() + 1
            self.lesson_number = utils.get_current_lesson_number()

    def __read_parameters(self, message):
        """
        Transform command parameters to class fields
        """
        if len(message.split()) > 1:
            for token in message.split()[1:]:
                self.parameters.append(token)
                if re.match("[A-zА-я]{2,4}[-]{0,1}[A-zА-я]{0,2}[0-9]{2,3}[A-zА-я]?(\(?[A-zА-я]*\)?)", token):
                    token = transliterate(token)
                    group_name = token
                    if '-' not in token:
                        group_name = token[:2] + '-' + token[2:]

                    self.group_id = utils.get_group_id_by_name(group_name)
                    if self.group_id == -2:
                        self.group_name = group_name
                        self.parameters.pop()
                elif re.match("[w][1|2]", token):
                    self.week = int(token[1])
                elif re.match("[w]", token):
                    self.week = datetime.date.today().isocalendar()[1] % 2 + 1
                elif utils.get_week_day(token):
                    self.day = utils.get_week_day(token)
                elif re.match("\b[1-6]\b", token):
                    self.lesson_number = int(token)
                elif re.match("[t]", token):
                    self.show_teacher = True
                elif re.match("[0-9]+", token):
                    self.teacher_id = int(token)
                elif re.match("[A-zА-я]+", token):
                    self.teacher_query += token if not self.teacher_query else (" " + token)
                else:
                    reply(self.chat_id, msg=self.responses['wrong_parameter'])
                    self.is_wrong_parameter = True

    def __check_parameters(self, command, parameters_number):
        if parameters_number > commands[command]:
            reply(self.chat_id, self.responses['wrong_parameters_number'])
        elif command != "/tt" and (self.week != 0 or self.day != 0 or self.lesson_number != 0):
            reply(self.chat_id, msg=self.responses['wrong_parameter'])
        elif (command != "/setteacher" and command != "/teacher") and (self.teacher_query != "" or self.teacher_id != 0):
            reply(self.chat_id, msg=self.responses['wrong_parameter'])
        elif (command == "/setteacher" or command == "/teacher") and self.teacher_id == 0 and self.teacher_query == "":
            reply(self.chat_id, msg=self.responses['no_required_parameter'])
        elif command == "/setgroup" and self.group_id == -1:
            reply(self.chat_id, msg=self.responses['unknown_group'])
        elif command == "/setgroup" and self.group_id == 0:
            reply(self.chat_id, msg=self.responses['no_required_parameter'])
        elif self.group_id == -2:
            query = Group.objects.all().filter(group_name__icontains=self.group_name + "(")
            keyboard = []
            for item in query:
                row = []
                # TODO: Hotfixed ")". Check.
                row.append("{0} {1}) ".format(command, item.group_name) + " ".join(self.parameters))
                keyboard.append(row)
            reply(self.chat_id, msg=self.responses['same_group'], keyboard=keyboard)

        elif command == "/tt" and self.day == 0:
            self.show_full_week = True
            self.is_wrong_parameter = False
        else:
            self.is_wrong_parameter = False

    def __check_day(self):
        # Custom reply for sunday
        if self.day == 7:
            reply(self.chat_id, self.responses['sunday'])
            return False

        # Check day existance
        if self.week not in self.timetable or\
           self.day not in self.timetable[self.week] or\
           not self.timetable[self.week][self.day]:
            if not self.show_full_week:
                reply(self.chat_id, msg=self.responses['get_tt_error'])
            return False
        elif self.day not in self.timetable[self.week] or self.timetable[self.week][self.day] == {}:
            if not self.show_full_week:
                reply(self.chat_id, msg=self.responses['get_tt_error'])
            return False
        return True

    def __show_day(self):
        """
        Shows timetable for whole day
        """
        if not self.__check_day():
            return

        # Add week day as title
        result = self.responses['week_days'][self.day]
        # Generate message body
        for lesson_number in self.timetable[self.week][self.day]:
            lesson = self.timetable[self.week][self.day][lesson_number]
            result += str(lesson_number) + ": " + lesson['discipline']['name'] + \
                (" (" + types[lesson['type']] + ")" if lesson['type'] else "") + " - "

            # Add rooms to response
            result += self.generate_rooms_string(lesson['rooms'])

            # If "T" parameter
            if self.show_teacher:
                if lesson['teachers']:
                    for teacher in lesson['teachers']:
                        result += "— " + teacher['name'] + "\n"
                else:
                    result += "— " + self.responses['no_teacher'] + "\n"

        reply(self.chat_id, msg=result)

    def __show_lesson(self, show_time_to_end=False):
        """
        Shows only one lesson
        """
        if not self.__check_day():
            return

        # Check lesson existance
        if self.lesson_number not in self.timetable[self.week][self.day]:
            reply(self.chat_id, msg=self.responses['no_lesson'])
            return

        # Generating message body
        lesson = self.timetable[self.week][self.day][self.lesson_number]

        result = self.responses['week_days'][self.day] + ":\n"
        result += str(self.lesson_number) + ": " + lesson['discipline']['name'] + " - "
        # Add rooms to response
        result += self.generate_rooms_string(lesson['rooms'])

        # Show teacher
        if self.show_teacher:
            if lesson['teachers']:
                for teacher in lesson['teachers']:
                    result += "— " + teacher['name'] + "\n"
            else:
                result += "— " + self.responses['no_teacher'] + "\n"

        # Add showing time to the end or lesson for /now command
        if show_time_to_end:
            now = datetime.datetime.now()
            time_to_end = str(int((pairs[self.lesson_number + 1] - now).total_seconds() // 60))
            reply(self.chat_id, msg=result + self.responses['minutes_left'].format(time_to_end))
        else:
            reply(self.chat_id, msg=result)

    def now_has_lesson(self):
        return get_current_lesson_number() in self.timetable[self.week][self.day]

    def now(self):
        self.__show_lesson(show_time_to_end=True)

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
        self.__show_lesson()

    def where(self):
        if not self.__check_day():
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

    def today(self):
        self.__show_day()

    def tomorrow(self):
        if self.day == 7:
            self.day = 1
            self.week = 3 - self.week
        else:
            self.day += 1

        self.__show_day()

    def tt(self):
        # To specify lesson number
        if self.lesson_number != 0:
            if self.day != 0 and self.week != 0:
                self.__show_lesson()
                return
            else:
                reply(self.chat_id, msg=self.responses['no_week_or_day'])
                return

        week_range = [self.week]
        if self.week == 0:
            if self.day != 0:
                reply(self.chat_id, msg=self.responses['no_week'])
                return
            week_range = list(range(1, 3))

        for self.week in week_range:
            reply(self.chat_id, msg="Week #" + str(self.week) + ":")
            if self.day == 0:
                for self.day in range(1, 7):
                    self.__show_day()
                self.day = 0
            else:
                self.__show_day()

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
        raw_response = requests.get(TIMETABLE_URL + "teachers/?search=%s}" % self.teacher_query)
        data = raw_response.json()

        # Check teacher existance
        if data['statusCode'] != 200:
            reply(self.chat_id, self.responses['unknown_teacher'])
            return

        # List all teachers that satisfy requirements
        teachers = data['data']
        if len(teachers) == 1:
            self.teacher_id = int(teachers[0]['id'])
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
                    row.append("/teacher %s" % teacher['teacher_id'])
                else:
                    row.append("/setteacher %s" % teacher['teacher_id'])
                keyboard.append(row)
                result += teacher['teacher_name'] + ' - ' + teacher['teacher_id'] + '\n'
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

    def generate_rooms_string(self, rooms):
        """
        Generate string like "339-19, 302-18" from rooms array
        """
        result = ""
        for room in rooms:
            room_name = "%s-%s" % (room['name'], room['building']['name'])
            result += room_name + ", "

        # Scrutch. TODO: think, how to optimise
        if result[-2] == ",":
            result = result[:-2]

        if not rooms:
            result += self.responses['unknown_room']
        result += "\n"


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
            raw_response = requests.get(TIMETABLE_URL + "groups/%i/timetable.json" % self.group_id)
            response = raw_response.json()
            if response['statusCode'] != 404:
                self.timetable = response['data']
                self.timetable = utils.prettify(self.timetable)
            else:
                reply(self.chat_id, msg=self.responses['no_timetable_for_group'])
                self.is_wrong_parameter = True
        except StopExecution:
            pass

    def who(self):
        # Check lesson existance
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

    def teachertt(self):
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
            raw_response = requests.get(TIMETABLE_URL + "teachers/%i/timetable.json" % self.teacher_id)
            response = raw_response.json()
            if response['statusCode'] == 200:
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

# Debug
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def test(request):
    try:
        tt = GroupTimetable(111791142, "/setgroup зв-зп41")
        tt.setgroup()
    except Exception:
        import traceback
        reply(111791142, msg=traceback.format_exc())
    from django.http import HttpResponse
    return HttpResponse()
