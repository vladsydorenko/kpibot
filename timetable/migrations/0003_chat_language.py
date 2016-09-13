# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('timetable', '0002_auto_20150820_2151'),
    ]

    operations = [
        migrations.AddField(
            model_name='chat',
            name='language',
            field=models.CharField(default=b'ru', max_length=3),
        ),
    ]
