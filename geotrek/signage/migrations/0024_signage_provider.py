# Generated by Django 3.1.14 on 2022-09-07 13:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('signage', '0023_auto_20220314_1441'),
    ]

    operations = [
        migrations.AddField(
            model_name='signage',
            name='provider',
            field=models.CharField(blank=True, max_length=1024, verbose_name='Provider'),
        ),
    ]
