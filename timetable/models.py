from django.db import models

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
