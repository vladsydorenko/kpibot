from django.db import models
from django.conf import settings
from django.utils.translation import ugettext as _

from timetable.exceptions import StopExecution
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
        """Get object corresponding to chat user type.

        Depending on chat user type return Group or Teacher
        object, or if we don't have predefined user type from this
        chat - stop execution.
        """
        if self.category == "group":
            return Group(resource_id=self.resource_id)
        elif self.category == "teacher":
            return Teacher(resource_id=self.resource_id)
        else:
            settings.BOT.sendMessage(self.id, text=_(
                "Группа или имя преподавателя по умолчанию не выставлены для этого чата"))
            raise StopExecution()
