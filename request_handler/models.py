from django.db import models

class Chat(models.Model):
    chat_id = models.CharField(max_length=30, primary_key=True)
    group = models.CharField(max_length=5, default="")
    language = models.CharField(max_length=3, default="ru")