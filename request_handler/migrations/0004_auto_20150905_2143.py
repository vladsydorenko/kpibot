# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('request_handler', '0003_chat_language'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chat',
            name='group',
            field=models.CharField(default='', max_length=5),
        ),
        migrations.AlterField(
            model_name='chat',
            name='language',
            field=models.CharField(default='ru', max_length=3),
        ),
    ]
