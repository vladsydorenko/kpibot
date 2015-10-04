# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('request_handler', '0004_auto_20150926_2224'),
    ]

    operations = [
        migrations.AddField(
            model_name='chat',
            name='teachers_id',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='chat',
            name='group',
            field=models.CharField(max_length=16, default=''),
        ),
    ]
