# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-12-14 07:46
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('standpoints', '0003_auto_20171129_0918'),
    ]

    operations = [
        migrations.AddField(
            model_name='standpoints',
            name='create_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]
