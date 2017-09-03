import abc
import logging
import re
from collections import defaultdict
from datetime import date, datetime

import telegram
from django.conf import settings
from django.utils.translation import ugettext as _

from timetable.api_client import KPIHubAPIClient
from timetable.exceptions import ParsingError, ValidationError, StopExecution


LESSON_TYPES = {
    0: 'Лек',
    1: 'Прак',
    2: 'Лаб'
}


WEEK_DAYS = {
    1: "Понедельник",
    2: "Вторник",
    3: "Среда",
    4: "Четверг",
    5: "Пятница",
    6: "Суббота",
}


WEEK_DAYS_ABBREVIATIONS = {
    1: ["mon", "pn"],
    2: ["tue", "vt"],
    3: ["wed", "sr"],
    4: ["thu", "cht"],
    5: ["fri", "pt"],
    6: ["sat", "sb"],
    7: ["sun", "vs"]
}


class TelegramCommand(metaclass=abc.ABCMeta):
    """Base class for all Telegram bot commands.

    `validation_schema` variable describes which arguments are required and which are optional for particular command
    It should be dict like:
        {
            'required': ['group'],
            'optional': ['day', 'week']
        }
    There are only 2 possible values:
        'required', which means that this parameter should always be in arguments.
        'optional', which means that it might be passed, but not always.
    All parameters that are not described in this dict will be processed as restricted for this command.
    `validate_not_allowed_arguments` enables or disables validation of not allowed arguments, so validation for
    required arguments are always performed, for not allowed - only when this flag is set to True.
    """
    validation_schema = {}
    validate_not_allowed_arguments = False

    def __init__(self, arguments, chat):
        self.chat = chat
        self.unparsed_arguments = arguments
        self.arguments = self.parse(arguments)
        self.set_default_values()

        self.validate_arguments()

    @abc.abstractproperty
    @property
    def command(self):
        """Every command class should describe what Telegram command it implements in `command` field"""
        pass

    @abc.abstractmethod
    def run(self):
        """Placeholder for implementing logic for particular command, each command must implement this method.

        On this stage we already have parsed and validated parameters.
        """
        pass

    def parse(self, arguments_list) -> dict:
        """Transform list of tokens to dict, when we know purpose of each argument.

        Possible parameters:
            kv-32, КВ32... - group code
            w1, w2 - week numbers
            w - current week number
            mon, tue, ..., fri - day number
            t - show teachers name
            1, 2, ..., 7 - lesson number
            Иванов Иван - teachers name
        IMPORTANT: on current stage we can only get group and teachers name. Then during validation
        they will be transformed to resource ids from API.
        """
        parsed_arguments = {}
        parsing_errors = []

        logging.info("Trying to parse list of arguments: {}".format(arguments_list))
        for token in arguments_list:
            # There are a really big variety of groups in database, like
            #   ма-61-1
            #   іо-56ін.
            #   мп-62-2(дммiом)
            #   жур-з71ф
            # We assume that group is a string that contains characters, numbers and has length more than 4.
            # It's much easier than construct regular expression for all cases.
            if re.search(r'\d', token) and re.search(r'\w', token) and len(token) >= 4:  # Group code
                self.unparsed_arguments.remove(token)
                parsed_arguments['group_name'] = self.transliterate(token)
                # To provide possibility to enter group code without '-'
                # we need to check it and manually insert into string.
                if '-' not in token:
                    insert_position = re.search("\d", token).start()
                    # Yet another dirty hack to process groups like ус-з51м
                    if parsed_arguments['group_name'][insert_position - 1] == 'з':
                        insert_position -= 1
                    parsed_arguments['group_name'] = parsed_arguments['group_name'][:insert_position] + '-' +\
                        parsed_arguments['group_name'][insert_position:]
            elif re.match('w[1|2]', token):
                parsed_arguments['week'] = int(token[1])
            elif token == 'w':  # current week number (1 or 2)
                parsed_arguments['week'] = self.current_educational_week()
            elif token == 't':
                parsed_arguments['print_teacher'] = True
            elif self.get_week_day(token):
                parsed_arguments['day'] = self.get_week_day(token)
            elif token.isdigit() and int(token) < 7:  # lesson number
                parsed_arguments['number'] = int(token)
            elif re.match(r'[А-яіїє]+', token):
                self.unparsed_arguments.remove(token)
                if 'teachers_name' not in parsed_arguments:
                    parsed_arguments['teachers_name'] = token
                else:
                    parsed_arguments['teachers_name'] += " " + token
            else:
                error_message = "{}: {}".format(_("Не могу понять что это за параметр"), token)
                parsing_errors.append(error_message)

        if not parsing_errors:
            return parsed_arguments
        else:
            raise ParsingError('\n'.join(parsing_errors))

    def set_default_values(self):
        """If some arguments wasn't explicitly passed - set some default values.

        For each command it might be group_id or teacher_id
        """
        if self.chat.category is not None:
            if self.chat.category == 'group' and 'group_name' not in self.arguments:
                self.arguments['groups'] = self.chat.resource_id
            elif self.chat.category == 'teacher' and 'teachers_name' not in self.arguments:
                self.arguments['teachers'] = self.chat.resource_id

    def validate_arguments(self):
        # Check existance of such group
        if 'group_name' in self.arguments:
            results = KPIHubAPIClient.find_group(self.arguments['group_name'])
            # When we search group in API, we might have 3 cases:
            if not results:  # We can't find such group
                raise ValidationError(_('Не могу найти такую группу. А ты уверен что ты знаешь где ты учишься?'))
            elif len(results) > 1:  # We have multiple groups that starts like passed value
                # In that case we construct custom keyboard with all possible choises of group
                # Important: we need self.unparsed_arguments to add all other arguments to created command
                custom_keyboard = []

                for group_object in results:
                    custom_keyboard.append(['{} {} {}'.format(self.command, group_object['name'],
                                                              ' '.join(self.unparsed_arguments))])
                    # If we have exact match - use it
                    if group_object['name'].lower() == self.arguments['group_name']:
                        self.arguments['groups'] = group_object['id']
                        del self.arguments['group_name']
                        break
                else:
                    self.reply(_('Тут есть несколько подходящих групп, выбери свою'), custom_keyboard)
                    raise StopExecution
            else:
                self.arguments['groups'] = results[0]['id']
                del self.arguments['group_name']

        # Check existance of such teacher
        if 'teachers_name' in self.arguments:
            results = KPIHubAPIClient.find_teacher(self.arguments['teachers_name'])
            if not results:
                raise ValidationError(_('Не могу найти преподавателя с таким именем. '
                                        'А ты точно написал его имя на украинском?'))
            elif len(results) > 1:
                custom_keyboard = [[
                    '{} {} {}'.format(self.command, teacher_object['name'], ' '.join(self.unparsed_arguments))]
                    for teacher_object in results
                    if teacher_object['name'].lower().startswith(self.arguments['teachers_name'])
                ]
                self.reply(_('Тут есть несколько подходящих преподавателей:'), custom_keyboard)
                raise StopExecution
            else:
                self.arguments['teachers'] = results[0]['id']
                del self.arguments['teachers_name']

        # Check if we have all required arguments
        for required_argument in self.validation_schema.get('required', []):
            if isinstance(required_argument, tuple) and not\
                        any([argument in self.arguments for argument in required_argument]):
                    raise ValidationError(_('Хей, ты не передал один из обязательных аргументов.'))
            elif isinstance(required_argument, str) and required_argument not in self.arguments:
                raise ValidationError(_('Хей, ты не передал один из обязательных аргументов.'))

        # Check if all other arguments are not restricted
        if self.validate_not_allowed_arguments:
            allowed_arguments = self.validation_schema.get('required', []) + self.validation_schema.get('optional', [])
            # Flatten allowed arguments (because single item might be tuple)
            for item in allowed_arguments:
                if isinstance(item, tuple):
                    allowed_arguments += list(item)
                    allowed_arguments.remove(item)

            if set(self.arguments.keys()) - set(allowed_arguments):
                raise ValidationError(_('Слушай, ну вот зачем ты мне лишние параметры для команды передаёшь?'))

    """ Utility functions """

    def reply(self, message, custom_keyboard=None):
        """Shortcut for sending text response to user"""
        if custom_keyboard:
            reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
        else:
            reply_markup = telegram.ReplyKeyboardRemove()
        settings.BOT.send_message(self.chat.id, text=message, parse_mode='Markdown', reply_markup=reply_markup)

    @staticmethod
    def transliterate(text: str) -> str:
        """Transliterate all english symbols to Ukrainian."""
        tr_en_ua = str.maketrans("abcdefghijklmnopqrstuvwxyz",
                                 "абцдефгхіжклмнопкрстуввхуз")
        return text.translate(tr_en_ua)

    @staticmethod
    def get_week_day(token: str) -> int:
        """Transform name of week day to its number."""
        for day_number, day_names in WEEK_DAYS_ABBREVIATIONS.items():
            if token in day_names:
                return day_number

    @staticmethod
    def current_educational_week(day=None) -> int:
        """Get number of educational week for some day.

        If day was not passed, we return educational week for today.
        """
        if not day:
            day = date.today()
        return 2 - day.isocalendar()[1] % 2


class TimetableTelegramCommand(TelegramCommand, metaclass=abc.ABCMeta):
    validate_not_allowed_arguments = True

    def run(self):
        query_parameters = self.arguments.copy()
        query_parameters['limit'] = 100
        raw_timetable = KPIHubAPIClient.get_timetable(query_parameters)

        if not raw_timetable:
            self.reply(_('Не могу найти пары. А они точно есть?'))
            return

        # Transform timetable to more convenient representation week -> day -> list of lesson objects
        self.timetable = defaultdict(lambda: defaultdict(list))
        for lesson in raw_timetable:
            lesson['formatted'] = self._format_lesson(lesson)
            self.timetable[lesson['week']][lesson['day']].append(lesson)

        self.process_timetable()

    def process_timetable(self):
        # Send formatted messages
        for week_number, week_timetable in self.timetable.items():
            for day, lessons_list in week_timetable.items():
                header = "*{}* ({} {}):\n".format(WEEK_DAYS[day], week_number, _("неделя"))
                self.reply(header + '\n'.join(sorted([lesson['formatted'] for lesson in lessons_list])))

    """ Utility functions """

    def _format_lesson(self, lesson: dict):
        """Format lesson object from API to readable form"""
        lesson_type = " (`{}`)".format(LESSON_TYPES[lesson['type']]) if lesson['type'] in LESSON_TYPES else ""

        rooms_string = ", ".join(lesson['rooms_full_names']) if lesson['rooms'] else _("расположение неизвестно")

        formatted_lesson = "*{}*: {}{} - {}".format(lesson['number'],
                                                    lesson['discipline_name'],
                                                    lesson_type,
                                                    rooms_string)

        # If "T" parameter has been passed, add teachers names to response.
        if self.arguments.get('print_teacher'):
            teachers_string = "\n  — ".join(lesson['teachers_short_names']) if lesson['teachers'] else _('не известно')
            formatted_lesson += "\n  — {}".format(teachers_string)
        return formatted_lesson

    @staticmethod
    def current_lesson_number():
        # TODO: Refactor
        now = datetime.now()
        pairs = [
            datetime(now.year, now.month, now.day, 0, 1),
            datetime(now.year, now.month, now.day, 8, 30),
            datetime(now.year, now.month, now.day, 10, 5),
            datetime(now.year, now.month, now.day, 12, 0),
            datetime(now.year, now.month, now.day, 13, 55),
            datetime(now.year, now.month, now.day, 15, 50),
            datetime(now.year, now.month, now.day, 17, 45),
            datetime(now.year, now.month, now.day, 23, 59)
        ]
        for i in range(len(pairs) - 1):
            if now > pairs[i] and now < pairs[i + 1]:
                return i
