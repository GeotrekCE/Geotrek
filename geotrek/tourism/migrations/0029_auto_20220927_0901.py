# Generated by Django 3.2.15 on 2022-09-27 09:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tourism', '0028_auto_20220927_0814'),
    ]

    operations = [
        migrations.AlterField(
            model_name='touristicevent',
            name='begin_date',
            field=models.DateField(verbose_name='Begin date'),
        ),
    ]
