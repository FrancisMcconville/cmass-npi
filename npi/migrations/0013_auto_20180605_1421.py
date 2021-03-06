# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-06-05 13:21
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('npi', '0012_auto_20180604_0931'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='supplier_info_state',
            field=models.CharField(choices=[('draft', 'Not Started'), ('rfq', 'Awaiting Upload'), ('complete', 'Quoted'), ('uploaded', 'Uploaded')], default='draft', max_length=16, verbose_name='Supplier Information State'),
        ),
        migrations.AlterField(
            model_name='projectsupplier',
            name='api_state',
            field=models.CharField(choices=[('ready', 'Ready'), ('error', 'Error!'), ('inactive', ''), ('pending', 'In-Progress'), ('finished', 'Complete'), ('finished_with_errors', 'Completed with Errors')], default='ready', max_length=20, verbose_name='Api State'),
        ),
        migrations.AlterField(
            model_name='suppliercomponent',
            name='state',
            field=models.CharField(choices=[('reject', 'Rejected'), ('normal', 'Accepted'), ('pending', 'Pending')], default='normal', max_length=16, verbose_name='State'),
        ),
    ]
