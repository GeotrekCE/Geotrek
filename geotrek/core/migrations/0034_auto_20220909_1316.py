# Generated by Django 3.1.14 on 2022-09-09 13:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0033_auto_20220728_0940'),
    ]

    operations = [
        migrations.AddField(
            model_name='path',
            name='provider',
            field=models.CharField(blank=True, db_index=True, max_length=1024, verbose_name='Provider'),
        ),
        migrations.AddField(
            model_name='trail',
            name='provider',
            field=models.CharField(blank=True, db_index=True, max_length=1024, verbose_name='Provider'),
        ),
    ]
