from django.db import models
from django.utils.translation import ugettext as _

from kpibot.utils import bot
from kpibot.utils.exceptions import StopExecution
from timetable.entities import Group, Teacher

LANGUAGE_CHOICES = (
    ('ru', 'ru'),
    ('uk', 'uk'),
)

CHAT_CATEGORY_CHOICES = (
    ('teacher', 'Teacher'),
    ('group', 'Group'),
)


class Chat(models.Model):
    id = models.IntegerField(primary_key=True)
    language = models.CharField(max_length=3,
                                choices=LANGUAGE_CHOICES,
                                default='ru')
    category = models.CharField(max_length=10,
                                choices=CHAT_CATEGORY_CHOICES,
                                null=True, blank=True)
    # Depends on category. Means group or teacher id in API.
    resource_id = models.IntegerField(null=True, blank=True)

    def get_entity(self):
        if self.category == "group":
            return Group(_id=self.resource_id)
        elif self.category == "teacher":
            return Teacher(_id=self.resource_id)
        else:
            bot.sendMessage(self.chat_id, text=_("Группа или имя преподавателя " +
                            "по умолчанию не выставлены для этого чата"))
            raise StopExecution()
