# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('timetable', '0007_remove_chat_group'),
    ]

    operations = [
        migrations.AddField(
            model_name='chat',
            name='remind',
            field=models.BooleanField(default=False),
        ),
    ]
