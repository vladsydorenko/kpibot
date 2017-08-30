from django.utils.translation import activate
from django.utils.translation import ugettext as _

from timetable.commands.base import TelegramCommand
from timetable.constants import HELP_TEXT, TIME


class HelpCommand(TelegramCommand):
    command = '/help'

    def run(self):
        self.reply(HELP_TEXT)


class TimeCommand(TelegramCommand):
    command = '/time'

    def run(self):
        self.reply(TIME)


class WeekCommand(TelegramCommand):
    command = '/week'

    def run(self):
        self.reply(_('Сейчас *{}* учебная неделя').format(self.current_educational_week()))


class ChangeLanguageCommand(TelegramCommand):
    command = '/changelang'

    def run(self):
        self.chat.language = 'uk' if self.chat.language == 'ru' else 'ru'
        self.chat.save()
        activate(self.chat.language)
        self.reply(_("Язык бота был изменён"))


class SetgroupCommand(TelegramCommand):
    command = '/setgroup'
    validation_schema = {
        'required': ['groups']
    }

    def set_default_values(self):
        pass

    def run(self):
        self.chat.category = 'group'
        self.chat.resource_id = self.arguments['groups']
        self.chat.save()
        self.reply(_("Я запомнил твою группу!"))


class SetteacherCommand(TelegramCommand):
    command = '/setteacher'
    validation_schema = {
        'required': ['teachers']
    }

    def set_default_values(self):
        pass

    def run(self):
        self.chat.category = 'teacher'
        self.chat.resource_id = self.arguments['teachers']
        self.chat.save()
        self.reply(_("Я запомнил твою группу!"))
