from django.db import models
from miscellaneous.utils import get_group_name_by_id

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
                                choices=CHAT_CATEGORY_CHOICES)
    # Depends on category. Means group or teacher id in API.
    resource_id = models.IntegerField(default=0)

    def __str__(self):
        return "{} - {}".format(self.chat_id,
                                get_group_name_by_id(self.group_id))
