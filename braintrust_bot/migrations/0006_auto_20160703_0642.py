# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-07-03 06:42
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('braintrust_bot', '0005_auto_20160510_0254'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChatGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField(max_length=100)),
                ('chat_id', models.BigIntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='ChatGroupMember',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.TextField(max_length=100)),
                ('chat_group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='braintrust_bot.ChatGroup')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='chatgroup',
            unique_together=set([('name', 'chat_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='chatgroupmember',
            unique_together=set([('username', 'chat_group')]),
        ),
    ]
