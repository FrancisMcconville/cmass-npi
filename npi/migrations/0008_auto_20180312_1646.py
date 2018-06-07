# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-03-12 16:46
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('npi', '0007_auto_20180308_1650'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='supplier_info_state',
            field=models.CharField(choices=[('complete', 'Quoted'), ('rfq', 'Awaiting Upload'), ('draft', 'Not Started'), ('uploaded', 'Uploaded')], default='draft', max_length=16, verbose_name='Supplier Information State'),
        ),
        migrations.AlterField(
            model_name='suppliercomponent',
            name='state',
            field=models.CharField(choices=[('reject', 'Rejected'), ('pending', 'Pending'), ('normal', 'Accepted')], default='normal', max_length=16, verbose_name='State'),
        ),
    ]
