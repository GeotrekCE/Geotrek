# Generated by Django 3.2.15 on 2022-09-26 13:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tourism', '0026_auto_20220907_1400'),
    ]

    operations = [
        migrations.AddField(
            model_name='touristicevent',
            name='bookable',
            field=models.BooleanField(default=False, verbose_name='Bookable'),
        ),
    ]