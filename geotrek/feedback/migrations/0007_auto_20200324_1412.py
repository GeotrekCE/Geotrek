# -*- coding: utf-8 -*-
# Generated by Django 1.11.27 on 2020-03-24 14:12
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feedback', '0006_auto_20200319_1311'),
    ]

    operations = [
        migrations.AddField(
            model_name='reportactivity',
            name='suricate_id',
            field=models.CharField(blank=True, default=None, max_length=50, null=True, verbose_name='Suricate id'),
        ),
        migrations.AddField(
            model_name='reportcategory',
            name='suricate_id',
            field=models.CharField(blank=True, default=None, max_length=50, null=True, verbose_name='Suricate id'),
        ),
        migrations.AddField(
            model_name='reportproblemmagnitude',
            name='suricate_id',
            field=models.CharField(blank=True, default=None, max_length=50, null=True, verbose_name='Suricate id'),
        ),
    ]
