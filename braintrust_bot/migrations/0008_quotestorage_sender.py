# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2017-05-15 19:07
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('braintrust_bot', '0007_quotestorage_location'),
    ]

    operations = [
        migrations.AddField(
            model_name='quotestorage',
            name='sender',
            field=models.TextField(blank=True, max_length=100, null=True),
        ),
    ]