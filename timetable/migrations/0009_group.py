# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('timetable', '0008_chat_remind'),
    ]

    operations = [
        migrations.CreateModel(
            name='Group',
            fields=[
                ('group_id', models.IntegerField(serialize=False, primary_key=True)),
                ('group_name', models.CharField(max_length=16, default='')),
            ],
        ),
    ]
