# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-06-06 10:06
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('npi', '0017_auto_20180606_1056'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='bom_state',
            field=models.CharField(choices=[('ready', 'Ready to Upload'), ('uploaded', 'Uploaded'), ('draft', 'Awaiting X/Y Data')], default='draft', max_length=16, verbose_name='State'),
        ),
        migrations.AlterField(
            model_name='project',
            name='supplier_info_state',
            field=models.CharField(choices=[('rfq', 'Awaiting Upload'), ('uploaded', 'Uploaded'), ('draft', 'Not Started'), ('complete', 'Quoted')], default='draft', max_length=16, verbose_name='Supplier Information State'),
        ),
        migrations.AlterField(
            model_name='projectsupplier',
            name='api_state',
            field=models.CharField(choices=[('finished', 'Complete'), ('error', 'Error!'), ('finished_with_errors', 'Completed with Errors'), ('inactive', ''), ('ready', 'Ready'), ('pending', 'In-Progress')], default='ready', max_length=20, verbose_name='Api State'),
        ),
    ]
