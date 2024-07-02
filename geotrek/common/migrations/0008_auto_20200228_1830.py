# -*- coding: utf-8 -*-
# Generated by Django 1.11.14 on 2020-02-28 17:30
from __future__ import unicode_literals


from django.conf import settings
from django.db import migrations


FIELDS = (
    ('theme', 'theme', 'label'),
)


def forward(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        for lang in settings.MODELTRANSLATION_LANGUAGES:
            for model, old, new in FIELDS:
                cursor.execute(
                    "SELECT 1 FROM information_schema.columns WHERE table_name='common_{}' AND column_name='{}_{}'".format(model, old, lang.replace('-', '_'))
                )
                if cursor.fetchone():
                    cursor.execute('ALTER TABLE common_{} RENAME {}_{} TO {}_{}'.format(model, old, lang.replace('-', '_'), new, lang.replace('-', '_')))


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0007_auto_20200228_1755'),
    ]

    operations = [
        migrations.RunPython(forward),
    ]
