from request_handler.models import Chat
# System libs
import re
import json
import requests
import datetime

# 3rd-party libs
from transliterate import translit
import logging
import traceback
import datetime

# Own modules
import miscellaneous.key
import miscellaneous.utils as utils
from miscellaneous.lang  import ru, ua
from miscellaneous.utils import reply
from miscellaneous.arrays import pairs, commands


class Timetable(object):
    chat_id = 0
    group_id = 0
    week = 0
    day = 0
    lesson_number = 0
    teacher_id = 0
    teacher_query = ""
    show_teacher = False
    show_full_week = False
    is_wrong_parameter = True

    timetable = {}
    responses = {}
    
    def __init__(self, chat_id, message):
        self.chat_id = chat_id
        
        # Set user language
        chat = Chat.objects.get(pk = chat_id)
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
                token = token.replace('-','')
                #TODO Change in new API
                """if not "ц" in token and not "(" in token:
                    token = utils.translit_ru_en(token)
                else:
                    self.group = token
                    continue"""
                # TODO: redo '-' paste for group with 3 letters on start
                if re.match("[A-zА-я][A-zА-я][A-zА-я]?[A-zА-я]?[0-9]+[A-zА-я]?\(?[A-zА-я]*\)?", token):
                    self.group_id = utils.get_group_id_by_name(token[:2] + '-' + token[2:])
                elif re.match("[w|W]", token):
                    self.week = datetime.date.today().isocalendar()[1] % 2 + 1
                elif re.match("[w|W][1|2]", token):
                    self.week = int(token[1])
                elif utils.get_week_day(token):
                    self.day = utils.get_week_day(token)
                elif re.match("\b[1-6]\b", token):
                    reply(self.chat_id, msg = token)
                    self.lesson_number = int(token)
                elif re.match("\b[t|T]\b", token):
                    self.show_teacher = True
                elif re.match("[0-9]+", token):
                    self.teacher_id = int(token)
                elif re.match("[A-zА-я]+", token):
                    self.teacher_query = token
                else:
                    reply(self.chat_id, msg = self.responses['wrong_parameter'])
                    self.is_wrong_parameter = True

    def __check_parameters(self, command, parameters_number):
        if parameters_number > commands[command]:
            reply(self.chat_id, self.responses['wrong_parameters_number'])
        elif command != "/tt" and (self.week != 0 or self.day != 0 or self.lesson_number != 0):
            reply(self.chat_id, msg = self.responses['wrong_parameter'])
        elif command != "/setteacher" and (self.teacher_query != "" or self.teacher_id != 0):
            reply(self.chat_id, msg = self.responses['wrong_parameter'])
        elif command == "/setteacher" and self.teacher_id == 0 and self.teacher_query == "":
            reply(self.chat_id, msg = self.responses['no_required_parameter'])
        elif command == "/setgroup" and self.group_id == 0:
            reply(self.chat_id, msg = self.responses['no_required_parameter'])
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
        if not self.week in self.timetable or\
           not self.day in self.timetable[self.week] or\
           not self.timetable[self.week][self.day]:
            if not self.show_full_week:
                reply(self.chat_id, msg = self.responses['get_tt_error'])
            return False
        elif not self.day in self.timetable[self.week] or self.timetable[self.week][self.day] == {}:
            if not self.show_full_week:
                reply(self.chat_id, msg = self.responses['get_tt_error'])
            return False
        return True

    def __show_day(self):
        """
        Shows timetable for whole day
        """
        if not self.__check_day():
            return

        # Generate message body
        result = ""
        for lesson_number in self.timetable[self.week][self.day]:
            lesson = self.timetable[self.week][self.day][lesson_number]
            result += lesson['lesson_number'] + ": " + lesson['lesson_name'] + \
            (" (" + lesson['lesson_type'] + ")" if lesson['lesson_type'] else "") + " - " + \
            (lesson['lesson_room'] if lesson['lesson_room'] else self.responses['unknown_room']) + "\n"

            # If "T" parameter
            if self.show_teacher:
                if len(lesson['teachers']) > 0:
                    for teacher in lesson['teachers']:
                        result += "--- " + teacher['teacher_full_name'] + "\n"
                else:
                    result += "--- " + self.responses['no_teacher'] + "\n"

        if result:
            # Add week day as title
            result = self.responses['week_days'][self.day] + ":\n" + result   
            reply(self.chat_id, msg = result)
        elif not self.show_full_week:
            reply(self.chat_id, msg = self.responses['get_tt_error'])
            
    
    def __show_lesson(self, show_time_to_end = False):
        """
        Shows only one lesson
        """
        if not self.__check_day():
            return

        # Check lesson existance
        if not self.lesson_number in self.timetable[self.week][self.day]:
            reply(self.chat_id, msg = self.responses['no_lesson'])
            return
            
        # Generating message body
        lesson = self.timetable[self.week][self.day][self.lesson_number]
        
        result = self.responses['week_days'][self.day] + ":\n"
        result += lesson['lesson_number'] + ": " + lesson['lesson_name'] + " - " + \
        (lesson['lesson_room'] if lesson['lesson_room']
                               else self.responses['unknown_room']) + "\n"

        # Show teacher
        if self.show_teacher:
            if len(lesson['teachers']) > 0:
                for teacher in lesson['teachers']:
                    result += "--- " + teacher['teacher_full_name'] + "\n"
            else:
                result += "--- " + self.responses['no_teacher'] + "\n"

        # Add showing time to the end or lesson for /now command
        if show_time_to_end:
            now = datetime.datetime.now()
            time_to_end = str((pairs[self.lesson_number + 1] - now).minutes)
            reply(self.chat_id, msg = result + self.responses['minutes_left'].format(time_to_end))
        else:
            reply(self.chat_id, msg = result)

        
    def now(self):
        self.__show_lesson(show_time_to_end = True)
        
    def next(self):
        # Get day with lessons (for satuday, sunday, etc.)
        while not self.day in self.timetable[self.week] or self.timetable[self.week][self.day] == {}:
            self.lesson_number = 0
            if self.day == 7:
                self.day = 1
                self.week = 3 - self.week
            else:
                self.day += 1            

        self.lesson_number += 1
        while not self.lesson_number in self.timetable[self.week][self.day]:
            self.lesson_number += 1

        self.__show_lesson()
        
    def where(self):
        if not self.__check_day():
            return

        # Check lesson existance
        if not self.lesson_number in self.timetable[self.week][self.day]:
            reply(self.chat_id, msg = self.responses['no_lesson'])
            return
            
        lesson = self.timetable[self.week][self.day][self.lesson_number]
        
        # Check if room set in timetable
        if not lesson['rooms']:
            reply(self.chat_id, msg = self.responses['no_room'])
            return

        coordinates = {}
        for room in lesson['rooms']:
            coordinates['longitude'] = float(room['room_longitude'])
            coordinates['latitude'] = float(room['room_latitude'])
            reply(self.chat_id, location = coordinates)

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
                reply(self.chat_id, msg = self.responses['no_week_or_day'])
                return

        week_range = [self.week]
        if self.week == 0:
            if self.day != 0:
                reply(self.chat_id, msg = self.responses['no_week'])
                return
            week_range = list(range(1,3)) 

        for self.week in week_range:
            reply(self.chat_id, msg = "Week #" + str(self.week) + ":")
            if self.day == 0:
                for self.day in range(1,7):
                    self.__show_day()
                self.day = 0
            else:
                self.__show_day()
                
    def setgroup(self):
        c = Chat(chat_id = self.chat_id,\
                 group_id = self.group_id,\
                 teacher_id = 0)
        c.save()
        reply(self.chat_id, msg = self.responses['setgroup_success'])

    def setteacher(self):
        if self.teacher_query:
            self.setteacher_query()
        else:
            self.setteacher_id()

    def setteacher_query(self):
        raw_data = requests.get("http://api.rozklad.org.ua/v2/teachers/?search={\'query\': \'%s\'}" % self.teacher_query)
        data = raw_data.json()
        
        # Check teacher existance
        if data['statusCode'] != 200:
            reply(self.chat_id, self.responses['unknown_teacher'])
            return
            
        # List all teachers that satisfy requirements
        teachers = data['data']
        result = self.responses['setteacher_filter']
        for teacher in teachers:
            result += teacher['teacher_name'] + ' - ' + str(teacher['teacher_id']) + '\n'
        reply(self.chat_id, msg = result)
    
    def setteacher_id(self):
        c = Chat(chat_id = self.chat_id,\
                 group_id = 0,\
                 teacher_id = self.teacher_id)
        c.save()
        reply(self.chat_id, msg = self.responses['setteacher_success'])


class GroupTimetable(Timetable):
    def __init__(self, chat_id, message):
        try:
            super().__init__(chat_id, message)
            if self.is_wrong_parameter:
                raise utils.StopException

            # Check if group exists
            if not utils.is_group_exists(self.group_id):
                reply(self.chat_id, msg = self.responses['unknown_group'])
                self.is_wrong_parameter = True
                raise utils.StopException

            # Check if group was set (by /setgroup or passed as parameter)
            if self.group_id == 0:
                chat = Chat.objects.get(pk = chat_id)
                self.group_id = chat.group_id
                
                if self.group_id == 0:
                    reply(self.chat_id, msg = self.responses['empty_group'])
                    self.is_wrong_parameter = True
                    raise utils.StopException
        
            # Get group timetable
            raw_data = requests.get("http://api.rozklad.org.ua/v2/groups/%i/timetable" % self.group_id)
            self.timetable = raw_data.json()['data']['weeks']
            self.timetable = self.prettify(self.timetable)
        except utils.StopException:
            pass

    def prettify(self, timetable):
        """
        Reformat timetable dict:
        From: self.timetable[str(week)]['days'][str(day)]['lessons'][str(lesson_number)]
        To:   self.timetable[week][day][lesson_number]
        """
        result = {}
        for week in timetable:
            result[int(week)] = {}
            for day in timetable[week]['days']:
                result[int(week)][int(day)] = {}
                for lesson in timetable[week]['days'][day]['lessons']:
                    result[int(week)][int(day)][int(lesson['lesson_number'])] = lesson
        return result

    def who(self):
        # Check lesson existance
        if not self.lesson_number in self.timetable[self.week][self.day]:
            reply(self.chat_id, msg = self.responses['no_lesson'])

        lesson = self.timetable[self.week][self.day][self.lesson_number]
        
        # Check if teachers set in timetable
        if not lesson['teachers']:
            reply(self.chat_id, msg = self.responses['no_teacher'])
        
        result = ""
        for teacher in lesson['teachers']:
            result += teacher['teacher_full_name'] + "\n"
            
        reply(self.chat_id, msg = result)

        
class TeacherTimetable(Timetable):
    def __init__(self, chat_id, message):
        try:
            super().__init__(chat_id, message)
            if self.is_wrong_parameter:
                raise utils.StopException
            
            command = message.split()[0].split('@')[0]
            if self.show_teacher or (self.group_id != 0 and command != "/setgroup"):
                reply(self.chat_id, msg = self.responses['wrong_parameter_for_teacher'])
                self.is_wrong_parameter = True
                raise utils.StopException

            if self.teacher_id == 0:
                chat = Chat.objects.get(pk = chat_id)
                self.teacher_id = chat.teacher_id
            
            # Get group timetable
            raw_data = requests.get("http://api.rozklad.org.ua/v2/teachers/%i/lessons" % self.teacher_id)
            data = raw_data.json()
            if data['statusCode'] == 200:
                self.timetable = data['data']
                self.timetable = self.prettify(self.timetable)
            else:
                if command not in ['/setgroup', '/setteacher']:
                    reply(self.chat_id, msg = self.responses['get_tt_error'])
                    self.is_wrong_parameter = True

        except utils.StopException:
            pass

    def prettify(self, timetable):
        """
        Reformat timetable from array to readable dict:
        self.timetable[week][day][lesson_number]
        """
        result = {}

        for week in range(1,3):
            result[week] = {}
            for day in range(1,7):
                result[week][day] = {}

        for lesson in timetable:
            result[int(lesson['lesson_week'])]\
                  [int(lesson['day_number'])]\
                  [int(lesson['lesson_number'])] = lesson
        return result

    def who(self):
        reply(self.chat_id, msg = self.responses['wrong_command_for_tm'])

# Debug
from django.views.decorators.csrf import csrf_exempt
@csrf_exempt
def test(request):
    TeacherTimetable(111791142, "/tomorrow").tomorrow()
    from django.http import HttpResponse
    return HttpResponse()