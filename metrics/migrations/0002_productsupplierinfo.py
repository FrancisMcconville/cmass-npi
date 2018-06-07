# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-06-06 10:06
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('metrics', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductSupplierinfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sequence', models.IntegerField(blank=True, null=True)),
                ('qty', models.DecimalField(blank=True, decimal_places=6, max_digits=1000, null=True)),
                ('delay', models.IntegerField(null=True, blank=True)),
                ('min_qty', models.FloatField(null=True, blank=True)),
                ('product_code', models.CharField(blank=True, max_length=64, null=True)),
                ('product_name', models.CharField(blank=True, max_length=128, null=True)),
                ('manufacturer_name', models.CharField(blank=True, max_length=64, null=True)),
                ('manufacturer_part_no', models.CharField(blank=True, max_length=32, null=True)),
                ('company', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='metrics.ResCompany')),
                ('name', models.ForeignKey(db_column='name', on_delete=django.db.models.deletion.DO_NOTHING, to='metrics.ResPartner')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='metrics.ProductProduct')),
            ],
            options={
                'managed': settings.IS_TESTING,
                'db_table': 'product_supplierinfo',
            },
        ),
    ]