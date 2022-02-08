# -*- coding: utf-8 -*-
# Generated by Django 1.11.14 on 2020-02-28 20:53
from django.conf import settings
from django.db import migrations


def forward(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        for lang in settings.MODELTRANSLATION_LANGUAGES:
            cursor.execute(
                f"SELECT 1 FROM information_schema.columns WHERE table_name='trekking_trek' AND column_name='disabled_infrastructure_{lang}'"
            )
            if cursor.fetchone():
                cursor.execute(f"UPDATE trekking_trek SET accessibility_infrastructure_{lang}=disabled_infrastructure_{lang} WHERE accessibility_infrastructure_{lang} = '';")
            cursor.execute(
                f"SELECT 1 FROM information_schema.columns WHERE table_name='trekking_trek' AND column_name='equipment_{lang}'"
            )
            if cursor.fetchone():
                cursor.execute(f"UPDATE trekking_trek SET gear_{lang}=equipment_{lang} WHERE equipment_{lang} = ''")


class Migration(migrations.Migration):

    dependencies = [
        ('trekking', '0038_auto_20220204_1537'),
    ]

    operations = [
        migrations.RunPython(forward),
    ]
