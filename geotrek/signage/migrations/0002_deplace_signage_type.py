# -*- coding: utf-8 -*-
# Generated by Django 1.11.14 on 2019-01-10 15:34
from __future__ import unicode_literals

from django.db import migrations


def deplace_data_signage_type(apps, schema_editor):
    # We can't import Infrastructure models directly as it may be a newer
    # version than this migration expects. We use the historical version.
    InfrastructureType = apps.get_model('infrastructure', 'InfrastructureType')
    SignageType = apps.get_model('signage', 'SignageType')
    for signage in InfrastructureType.objects.all().values():
        del signage['pk']
        SignageType.objects.create(**signage)


class Migration(migrations.Migration):

    dependencies = [
        ('signage', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(deplace_data_signage_type)
    ]
