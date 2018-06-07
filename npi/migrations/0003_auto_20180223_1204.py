# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-02-23 12:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('npi', '0002_auto_20180222_0903'),
    ]

    operations = [
        migrations.AddField(
            model_name='component',
            name='uom_name',
            field=models.CharField(default=1, max_length=16, verbose_name='UOM'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='suppliercomponent',
            name='uom_name',
            field=models.CharField(default=1, max_length=16, verbose_name='UOM'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='supplierproductquote',
            name='selected',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='project',
            name='supplier_info_state',
            field=models.CharField(choices=[('rfq', 'Awaiting Upload'), ('draft', 'Not Started'), ('complete', 'Complete')], default='draft', max_length=16, verbose_name='Supplier Information State'),
        ),
    ]