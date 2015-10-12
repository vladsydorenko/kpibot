from django.db import models
from miscellaneous.utils import get_group_by_id

class Chat(models.Model):
    chat_id = models.IntegerField(primary_key=True)
    language = models.CharField(max_length=3, default="ru")
    teacher_id = models.IntegerField(default=0)
    group_id = models.IntegerField(default=0)
    remind = models.BooleanField(default=False)

    def __str__(self):
        return str(self.chat_id) + " - " + get_group_by_id(self.group_id)