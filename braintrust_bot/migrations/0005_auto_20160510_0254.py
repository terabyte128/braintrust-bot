# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-05-10 02:54
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('braintrust_bot', '0004_auto_20160507_0633'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chatmember',
            name='chat_id',
            field=models.BigIntegerField(),
        ),
        migrations.AlterField(
            model_name='quotechat',
            name='chat_id',
            field=models.BigIntegerField(unique=True),
        ),
        migrations.AlterField(
            model_name='quotestorage',
            name='chat_id',
            field=models.BigIntegerField(),
        ),
    ]