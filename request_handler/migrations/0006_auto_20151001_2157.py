# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('request_handler', '0005_auto_20150927_2116'),
    ]

    operations = [
        migrations.RenameField(
            model_name='chat',
            old_name='teachers_id',
            new_name='teacher_id',
        ),
        migrations.AddField(
            model_name='chat',
            name='group_id',
            field=models.IntegerField(default=0),
        ),
    ]
