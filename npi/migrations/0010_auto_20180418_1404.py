# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-04-18 13:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('npi', '0009_auto_20180410_1018'),
    ]

    operations = [
        migrations.AddField(
            model_name='projectsupplier',
            name='upload_date',
            field=models.DateTimeField(null=True),
        ),
    ]
